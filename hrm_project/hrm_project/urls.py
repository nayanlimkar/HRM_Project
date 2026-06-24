from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from hrm import views
from hrm.views import leave_page
from django.contrib.auth import views as auth_views


router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet)
router.register(r'departments', views.DepartmentViewSet)
router.register(r'attendance', views.AttendanceViewSet)
router.register(r'leave', views.LeaveViewSet)

urlpatterns = [
    path('', views.home),

    path('leave-ui/', leave_page),
    path('employees-ui/', views.employees_page),
    path('departments-ui/', views.departments_page),
    path('attendance-ui/', views.attendance_page),
    path('attendance-ui/', views.attendance_page, name='attendance_page'),

    path('add-department/', views.add_department),
    path('add-employee/', views.add_employee),
    path('edit-employee/<int:id>/', views.edit_employee),
    path('delete-employee/<int:id>/', views.delete_employee),

    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api-auth/', include('rest_framework.urls')),
    path('approve-leave/<int:id>/', views.approve_leave),
    path('leave-ui/', views.leave_page, name='leave_page'),
    path('reject-leave/<int:id>/', views.reject_leave),

    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),

    path('logout/', auth_views.LogoutView.as_view(), name='logout'),


    # payroll
    path('payroll/', views.payroll_list, name='payroll_list'),
    path('payroll/add/', views.payroll_add, name='payroll_add'),
    path('payroll/delete/<int:pk>/', views.payroll_delete, name='payroll_delete'),

    path('payroll/mark-paid/<int:pk>/', views.payroll_mark_paid, name='payroll_mark_paid'),


]
