from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Author, Book, Member, Loan
from .serializers import AuthorSerializer, BookSerializer, MemberSerializer, LoanSerializer
from rest_framework.decorators import action
from django.utils import timezone
from .tasks import send_loan_notification
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging
from django.db import connection
class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    
    def get_queryset(self):
        """
        Optimized queryset that uses select_related to minimize database queries.
        """
        return Book.objects.select_related('author')
    
    def list(self, request, *args, **kwargs):
        """
        Override list method to verify query optimization using Django's debug tools.
        """
        initial_query_count = len(connection.queries)
        response = super().list(request, *args, **kwargs)
        queries_executed = len(connection.queries) - initial_query_count
        
        logger = logging.getLogger(__name__)
        logger.info(f"BookViewSet executed {queries_executed} database queries for retrieving books with authors")
        
        return response

    @action(detail=True, methods=['post'])
    def loan(self, request, pk=None):
        book = self.get_object()
        if book.available_copies < 1:
            return Response({'error': 'No available copies.'}, status=status.HTTP_400_BAD_REQUEST)
        member_id = request.data.get('member_id')
        try:
            member = Member.objects.get(id=member_id)
        except Member.DoesNotExist:
            return Response({'error': 'Member does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan = Loan.objects.create(book=book, member=member)
        book.available_copies -= 1
        book.save()
        send_loan_notification.delay(loan.id)
        return Response({'status': 'Book loaned successfully.'}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def return_book(self, request, pk=None):
        book = self.get_object()
        member_id = request.data.get('member_id')
        try:
            loan = Loan.objects.get(book=book, member__id=member_id, is_returned=False)
        except Loan.DoesNotExist:
            return Response({'error': 'Active loan does not exist.'}, status=status.HTTP_400_BAD_REQUEST)
        loan.is_returned = True
        loan.return_date = timezone.now().date()
        loan.save()
        book.available_copies += 1
        book.save()
        return Response({'status': 'Book returned successfully.'}, status=status.HTTP_200_OK)

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

    @action(detail=True, methods=['post'])
    def extend_due_date(self, request, pk=None):

        loan = self.get_object()
        additional_days = request.data.get('additional_days')
        if timezone.now().date() < loan.due_date:
            return Response({'error': 'Already loan overdue, So can not extend date.'}, status=status.HTTP_400_BAD_REQUEST)

        extended_due_date = loan.due_date.date() + timedelta(days=additional_days)
        loan.due_date = extended_due_date
        loan.save()
        serializer = self.get_serializer(loan)
        return Response({
            'loan': serializer.data
        }, status=status.HTTP_200_OK)






