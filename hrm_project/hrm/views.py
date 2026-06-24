from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
import json

from rest_framework import viewsets

from .models import Employee, Department, Attendance, Leave
from .serializers import EmployeeSerializer, DepartmentSerializer, AttendanceSerializer, LeaveSerializer
from .forms import DepartmentForm, EmployeeForm
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from itertools import groupby
from .models import Payroll, Department
from .forms import PayrollForm
from django.db.models.functions import TruncMonth
from django.db.models import Count, Q

@login_required

def home(request):
    dept_data = Department.objects.annotate(count=Count('employee'))
    dept_labels = [d.name for d in dept_data]
    dept_counts = [d.count for d in dept_data]

    attendance_data = Attendance.objects.values('status').annotate(count=Count('status'))
    att_labels = [a['status'] for a in attendance_data]
    att_counts = [a['count'] for a in attendance_data]

    leave_data = Leave.objects.values('status').annotate(count=Count('status'))
    leave_labels = [l['status'] for l in leave_data]
    leave_counts = [l['count'] for l in leave_data]

    return render(request, 'home.html', {
        'dept_labels': json.dumps(dept_labels),
        'dept_counts': json.dumps(dept_counts),
        'att_labels': json.dumps(att_labels),
        'att_counts': json.dumps(att_counts),
        'leave_labels': json.dumps(leave_labels),
        'leave_counts': json.dumps(leave_counts),
    })


def employees_page(request):

    search = request.GET.get('search')

    employees = Employee.objects.all()

    # SEARCH
    if search:
        employees = employees.filter(name__icontains=search)

    # PAGINATION
    paginator = Paginator(employees, 10)   # 10 employees per page

    page_number = request.GET.get('page')
    employees = paginator.get_page(page_number)

    return render(request, 'employees.html', {
        'employees': employees
    })


def add_employee(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/employees-ui/')
    else:
        form = EmployeeForm()
    return render(request, 'add_employee.html', {'form': form})


def edit_employee(request, id):
    employee = get_object_or_404(Employee, id=id)
    if request.method == 'POST':
        form = EmployeeForm(request.POST, instance=employee)
        if form.is_valid():
            form.save()
            return redirect('/employees-ui/')
    else:
        form = EmployeeForm(instance=employee)
    return render(request, 'add_employee.html', {'form': form})


def delete_employee(request, id):
    employee = get_object_or_404(Employee, id=id)
    employee.delete()
    return redirect('/employees-ui/')


def departments_page(request):
    departments = Department.objects.all()
    return render(request, 'departments.html', {'departments': departments})


def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/departments-ui/')
    else:
        form = DepartmentForm()
    return render(request, 'add_department.html', {'form': form})




def attendance_page(request):
    departments = Department.objects.all()
    
    selected_dept = request.GET.get('dept', '')
    selected_month = request.GET.get('month', '')  # format: YYYY-MM

    attendance = Attendance.objects.select_related('employee', 'employee__department')

    if selected_dept:
        attendance = attendance.filter(employee__department__id=selected_dept)

    if selected_month:
        year, month = selected_month.split('-')
        attendance = attendance.filter(date__year=year, date__month=month)

    # Group by department → employee → records
    dept_data = {}
    for att in attendance.order_by('employee__department__name', 'employee__name', 'date'):
        dept = att.employee.department
        dept_name = dept.name if dept else 'No Department'
        dept_id = dept.id if dept else 0

        if dept_id not in dept_data:
            dept_data[dept_id] = {
                'name': dept_name,
                'employees': {}
            }

        emp = att.employee
        if emp.id not in dept_data[dept_id]['employees']:
            dept_data[dept_id]['employees'][emp.id] = {
                'name': emp.name,
                'records': [],
                'present': 0,
                'absent': 0,
            }

        dept_data[dept_id]['employees'][emp.id]['records'].append(att)

        status_lower = att.status.lower()
        if status_lower == 'present':
            dept_data[dept_id]['employees'][emp.id]['present'] += 1
        elif status_lower == 'absent':
            dept_data[dept_id]['employees'][emp.id]['absent'] += 1

    return render(request, 'attendance.html', {
        'dept_data': dept_data,
        'departments': departments,
        'selected_dept': selected_dept,
        'selected_month': selected_month,
    })


def leave_page(request):
    departments = Department.objects.all()

    selected_dept = request.GET.get('dept', '')
    selected_month = request.GET.get('month', '')  # format: YYYY-MM

    leaves = Leave.objects.select_related('employee', 'employee__department')

    if selected_dept:
        leaves = leaves.filter(employee__department__id=selected_dept)

    if selected_month:
        year, month = selected_month.split('-')
        leaves = leaves.filter(start_date__year=year, start_date__month=month)

    # Group by department → employee → records
    dept_data = {}
    for leave in leaves.order_by('employee__department__name', 'employee__name', 'start_date'):
        dept = leave.employee.department
        dept_name = dept.name if dept else 'No Department'
        dept_id = dept.id if dept else 0

        if dept_id not in dept_data:
            dept_data[dept_id] = {
                'name': dept_name,
                'employees': {}
            }

        emp = leave.employee
        if emp.id not in dept_data[dept_id]['employees']:
            dept_data[dept_id]['employees'][emp.id] = {
                'name': emp.name,
                'records': [],
                'approved': 0,
                'pending': 0,
                'rejected': 0,
            }

        dept_data[dept_id]['employees'][emp.id]['records'].append(leave)

        status_lower = leave.status.lower()
        if status_lower == 'approved':
            dept_data[dept_id]['employees'][emp.id]['approved'] += 1
        elif status_lower == 'pending':
            dept_data[dept_id]['employees'][emp.id]['pending'] += 1
        elif status_lower == 'rejected':
            dept_data[dept_id]['employees'][emp.id]['rejected'] += 1

    return render(request, 'leave.html', {
        'dept_data': dept_data,
        'departments': departments,
        'selected_dept': selected_dept,
        'selected_month': selected_month,
    })




class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer


class LeaveViewSet(viewsets.ModelViewSet):
    queryset = Leave.objects.all()
    serializer_class = LeaveSerializer



def approve_leave(request, id):

    leave = Leave.objects.get(id=id)

    leave.status = "Approved"
    leave.save()

    #  SEND EMAIL
    send_mail(
        subject='Leave Approved',
        
        message=f'Hello {leave.employee.name}, your leave has been approved.',

        from_email=settings.EMAIL_HOST_USER,

        recipient_list=[leave.employee.email],

        fail_silently=False,
    )

    return redirect('/leave-ui/')

def reject_leave(request, id):
    leave = Leave.objects.get(id=id)
    leave.status = "Rejected"
    leave.save()
    return redirect('/leave-ui/')




def payroll_list(request):
    month = request.GET.get('month', '')
    payrolls = Payroll.objects.select_related('employee', 'employee__department').order_by(
        'employee__department__name', 'employee__name'
    )
    if month:
        payrolls = payrolls.filter(month=month)

    # Group by department
    dept_data = {}
    for p in payrolls:
        dept = p.employee.department.name if p.employee.department else 'No Department'
        if dept not in dept_data:
            dept_data[dept] = {'payrolls': [], 'total': 0}
        dept_data[dept]['payrolls'].append(p)
        dept_data[dept]['total'] += p.net_salary

    total_payout = sum(d['total'] for d in dept_data.values())
    pending_count = payrolls.filter(status='pending').count()

    return render(request, 'payroll.html', {
        'dept_data': dept_data,
        'total_payout': total_payout,
        'pending_count': pending_count,
        'total_employees': payrolls.count(),
        'selected_month': month,
    })

def payroll_add(request):
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payroll_list')
    else:
        form = PayrollForm()

    departments = Department.objects.prefetch_related('employee_set').all()
    return render(request, 'payroll_form.html', {
        'form': form,
        'departments': departments,
    })


def payroll_delete(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    if request.method == 'POST':
        payroll.delete()
    return redirect('payroll_list')

def payroll_mark_paid(request, pk):
    payroll = get_object_or_404(Payroll, pk=pk)
    payroll.status = 'paid'
    payroll.save()
    return redirect('payroll_list')