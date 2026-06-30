from app.models.report import Report, ReportStatus, ReportReason
from app.models.user import User, AccountStatus, UserType
from app.models.review import Review
from app.models.comment import Comment
from app.services.notification_service import NotificationService
from app import db
from datetime import datetime, timedelta

class AdminService:
    
    @staticmethod
    def get_pending_reports(page=1, per_page=20):
        """Get all pending reports"""
        query = Report.query.filter_by(status=ReportStatus.PENDING)
        return query.order_by(Report.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def get_all_reports(page=1, per_page=20, status=None):
        """Get reports with optional status filter"""
        query = Report.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Report.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
    
    @staticmethod
    def handle_report(report_id, admin_id, action, notes=None):
        """Handle a report"""
        report = Report.query.get(report_id)
        if not report:
            return False, 'Report not found'
        
        if report.status != ReportStatus.PENDING:
            return False, 'Report already handled'
        
        # Take action on the reported user
        reported_user = report.reported_user
        
        if action == 'dismiss':
            report.status = ReportStatus.DISMISSED
            report.handled_by_id = admin_id
            report.admin_notes = notes
            report.resolved_at = datetime.utcnow()
            message = 'Report dismissed'
            
        elif action == 'warning':
            report.status = ReportStatus.RESOLVED
            report.handled_by_id = admin_id
            report.admin_notes = notes
            report.resolved_at = datetime.utcnow()
            # Issue warning (just track in notes for now)
            message = 'Warning issued'
            
        elif action.startswith('suspend_'):
            days = int(action.split('_')[1].replace('days', ''))
            report.status = ReportStatus.RESOLVED
            report.handled_by_id = admin_id
            report.admin_notes = notes
            report.resolved_at = datetime.utcnow()
            
            # Suspend user
            reported_user.account_status = AccountStatus.SUSPENDED
            # In a real system, you'd set a suspension expiry date
            message = f'User suspended for {days} days'
            
        elif action == 'permanent_ban':
            report.status = ReportStatus.RESOLVED
            report.handled_by_id = admin_id
            report.admin_notes = notes
            report.resolved_at = datetime.utcnow()
            
            # Ban user permanently
            reported_user.account_status = AccountStatus.DEACTIVATED
            message = 'User permanently banned'
            
        elif action == 'deactivate':
            report.status = ReportStatus.RESOLVED
            report.handled_by_id = admin_id
            report.admin_notes = notes
            report.resolved_at = datetime.utcnow()
            
            # Deactivate user
            reported_user.account_status = AccountStatus.DEACTIVATED
            message = 'User account deactivated'
            
        else:
            return False, 'Invalid action'
        
        # Increment report count on user (if action is not dismiss)
        if action != 'dismiss':
            reported_user.increment_reports(report.reason.value)
            
            # Check if user should be auto-deactivated
            if reported_user.check_deactivation_criteria():
                db.session.commit()
                # Notify user of deactivation
                NotificationService.create_notification(
                    user_id=reported_user.id,
                    notification_type='account_status_change',
                    title='Account deactivated',
                    message=f'Your account has been automatically deactivated due to multiple reports.',
                    metadata={'reason': reported_user.deactivation_reason}
                )
        
        db.session.commit()
        
        # Notify the reported user of the action
        if action != 'dismiss':
            NotificationService.create_notification(
                user_id=reported_user.id,
                notification_type='report_resolved',
                title=f'Report resolved: {message}',
                message=f'Action taken: {message}',
                metadata={'report_id': report.id, 'action': action}
            )
        
        # Notify the reporter
        NotificationService.create_notification(
            user_id=report.reporter_id,
            notification_type='report_resolved',
            title=f'Your report has been resolved',
            message=f'Report #{report.id} has been resolved. Action taken: {message}',
            metadata={'report_id': report.id, 'action': action}
        )
        
        return True, message
    
    @staticmethod
    def get_platform_stats():
        """Get overall platform statistics"""
        total_users = User.query.count()
        total_reviews = Review.query.count()
        total_comments = Comment.query.count()
        
        # Active users (logged in within last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        active_users = User.query.filter(User.last_login >= week_ago).count()
        
        # Reports
        pending_reports = Report.query.filter_by(status=ReportStatus.PENDING).count()
        resolved_reports = Report.query.filter_by(status=ReportStatus.RESOLVED).count()
        
        # Reviews by type
        reviewer_count = User.query.filter_by(user_type=UserType.REVIEWER).count()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_reviews': total_reviews,
            'total_comments': total_comments,
            'pending_reports': pending_reports,
            'resolved_reports': resolved_reports,
            'reviewer_count': reviewer_count,
            'regular_user_count': total_users - reviewer_count
        }
    
    @staticmethod
    def manage_user(user_id, action, notes=None):
        """Admin action on a user"""
        user = User.query.get(user_id)
        if not user:
            return False, 'User not found'
        
        if action == 'suspend':
            user.account_status = AccountStatus.SUSPENDED
            message = 'User suspended'
        elif action == 'activate':
            user.account_status = AccountStatus.ACTIVE
            message = 'User activated'
        elif action == 'deactivate':
            user.account_status = AccountStatus.DEACTIVATED
            message = 'User deactivated'
        elif action == 'make_reviewer':
            user.user_type = UserType.REVIEWER
            message = 'User upgraded to reviewer'
        elif action == 'make_regular':
            user.user_type = UserType.REGULAR
            message = 'User downgraded to regular'
        else:
            return False, 'Invalid action'
        
        user.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Notify user
        NotificationService.create_notification(
            user_id=user.id,
            notification_type='account_status_change',
            title=f'Account updated: {message}',
            message=f'An administrator has updated your account: {message}',
            metadata={'action': action, 'notes': notes}
        )
        
        return True, message
    
    @staticmethod
    def delete_report(report_id):
        """Delete a report (admin only)"""
        report = Report.query.get(report_id)
        if not report:
            return False, 'Report not found'
        
        db.session.delete(report)
        db.session.commit()
        return True, 'Report deleted'