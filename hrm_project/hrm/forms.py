from django import forms
from .models import Department, Employee
from .models import Payroll


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['name', 'email', 'salary', 'joining_date', 'department']


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'location'] 


class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        fields = ['employee', 'month', 'basic_salary', 'bonus', 'deductions', 'status']
        widgets = {
            'employee': forms.Select(attrs={'class': 'form-control'}),
            'month': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. May 2026'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'bonus': forms.NumberInput(attrs={'class': 'form-control'}),
            'deductions': forms.NumberInput(attrs={'class': 'form-control'}),
        }
