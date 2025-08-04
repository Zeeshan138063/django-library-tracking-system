from celery import shared_task
from .models import Loan
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)



@shared_task
def send_loan_notification(loan_id):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        book_title = loan.book.title
        send_mail(
            subject='Book Loaned Successfully',
            message=f'Hello {loan.member.user.username},\n\nYou have successfully loaned "{book_title}".\nPlease return it by the due date.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass

"""
    Create a Celery Periodic Task:
    Define a task named check_overdue_loans that executes daily.
    The task should:
    Query all loans where is_returned is False and due_date is past.
    Send an email reminder to each member with overdue books.
"""

@shared_task
def check_overdue_loans():
#     """
#     Create a Celery Periodic Task:
# Define a task named check_overdue_loans that executes daily.
# The task should:
# Query all loans where is_returned is False and due_date is past.
# Send an email reminder to each member with overdue books.
#     """
    logger.info("Starting overdue books check...")

    try:
        # Calculate cutoff date (books overdue by more than 14 days)
        cutoff_date = timezone.now().date() - timedelta(days=14)

        # Find overdue loans
        overdue_loans = Loan.objects.filter(
            is_returned=False,
            due_date__lt=cutoff_date
        ).select_related('book', 'member__user')

        overdue_count = overdue_loans.count()
        logger.info(f"Found {overdue_count} overdue books")

        # Process each overdue loan
        processed_notifications = 0
        for loan in overdue_loans:
            try:
                # Calculate days overdue
                days_overdue = (timezone.now().date() - loan.loan_date).days
                message = f"Hello {loan.member.user.username},\n\nYou have Overdue book: '{loan.book.title}' borrowed by {loan.member.user.username} - {days_overdue} days overdue, Please return it."
                # Log the overdue book
                logger.warning(message)
                send_reminder_overdue_book_notification.delay(loan.id,message)
                # check_overdue_loans
                processed_notifications += 1

            except Exception as e:
                logger.error(f"Error processing loan {loan.id}: {str(e)}")

        # Return summary
        result = {
            'task_name': 'check_overdue_books',
            'timestamp': timezone.now().isoformat(),
            'overdue_count': overdue_count,
            'processed_notifications': processed_notifications,
            'status': 'completed'
        }

        logger.info(f"Overdue books check completed: {result}")
        return result

    except Exception as e:
        error_result = {
            'task_name': 'check_overdue_books',
            'timestamp': timezone.now().isoformat(),
            'error': str(e),
            'status': 'failed'
        }
        logger.error(f"Overdue books check failed: {error_result}")
        return error_result



@shared_task
def send_reminder_overdue_book_notification(loan_id, message):
    try:
        loan = Loan.objects.get(id=loan_id)
        member_email = loan.member.user.email
        send_mail(
            subject='Book Overdue ',
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[member_email],
            fail_silently=False,
        )
    except Loan.DoesNotExist:
        pass

