from django.contrib import admin
from django import forms
from .models import Employee, Department, Attendance, Leave, Payroll


admin.site.site_header = "Administration"
admin.site.site_title = "Administration Portal"
admin.site.index_title = "Welcome to Administration"


# ── Department-grouped employee dropdown ──────────────────────────────────────
class AttendanceAdminForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Build grouped choices: [(dept_name, [(emp_id, emp_name), ...]), ...]
        grouped = []
        for dept in Department.objects.prefetch_related('employee_set').order_by('name'):
            employees = dept.employee_set.order_by('name')
            if employees.exists():
                choices = [(emp.id, emp.name) for emp in employees]
                grouped.append((dept.name, choices))

        self.fields['employee'].choices = [('', '---------')] + grouped


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    form = AttendanceAdminForm
    list_display  = ['employee', 'get_department', 'date', 'status']
    list_filter   = ['employee__department', 'status', 'date']
    search_fields = ['employee__name', 'employee__department__name']
    ordering      = ['-date']

    def get_department(self, obj):
        return obj.employee.department.name if obj.employee.department else '—'
    get_department.short_description = 'Department'


# ── Rest of models ─────────────────────────────────────────────────────────────
admin.site.register(Employee)
admin.site.register(Department)
admin.site.register(Leave)


@admin.register(Payroll)
class PayrollAdmin(admin.ModelAdmin):
    list_display  = ['employee', 'month', 'basic_salary', 'bonus', 'deductions', 'net_salary']
    search_fields = ['employee__name', 'month']