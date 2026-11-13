from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
)
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .forms import SignUpForm, TaskForm
from .models import Task


# -------------------------
# User Registration
# -------------------------

class SignUpView(View):
    template_name = "registration/signup.html"

    def get(self, request):
        form = SignUpForm()

        return render(
            request,
            self.template_name,
            {"form": form},
        )

    def post(self, request):
        form = SignUpForm(request.POST)

        if form.is_valid():
            user = form.save()

            login(request, user)

            messages.success(
                request,
                "Your account has been created successfully.",
            )

            return redirect("dashboard")

        return render(
            request,
            self.template_name,
            {"form": form},
        )


# -------------------------
# Login and Logout
# -------------------------

class CustomLoginView(LoginView):
    template_name = "registration/login.html"
    redirect_authenticated_user = True


class CustomLogoutView(LogoutView):
    next_page = "login"


# -------------------------
# Dashboard
# -------------------------

class DashboardView(LoginRequiredMixin, View):

    def get(self, request):
        user_tasks = Task.objects.filter(
            owner=request.user
        )

        context = {
            "total": user_tasks.count(),
            "completed": user_tasks.filter(
                is_completed=True
            ).count(),
            "pending": user_tasks.filter(
                is_completed=False
            ).count(),
        }

        return render(
            request,
            "tasks/dashboard.html",
            context,
        )


# -------------------------
# Display Tasks
# -------------------------

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = "tasks/task_list.html"
    context_object_name = "tasks"
    paginate_by = 10

    def get_queryset(self):
        queryset = Task.objects.select_related(
            "category",
            "owner",
        )

        if self.request.user.is_staff:
            return queryset

        return queryset.filter(
            owner=self.request.user
        )


# -------------------------
# View Task Details
# -------------------------

class TaskDetailView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DetailView,
):
    model = Task
    template_name = "tasks/task_detail.html"
    context_object_name = "task"

    def test_func(self):
        task = self.get_object()

        return (
            self.request.user.is_staff
            or task.owner_id == self.request.user.id
        )

    def handle_no_permission(self):
        messages.error(
            self.request,
            "You do not have permission to view that task.",
        )

        return redirect("task_list")


# -------------------------
# Create Task
# -------------------------

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def form_valid(self, form):
        form.instance.owner = self.request.user

        messages.success(
            self.request,
            "Task created successfully.",
        )

        return super().form_valid(form)


# -------------------------
# Update Task
# -------------------------

class TaskUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateView,
):
    model = Task
    form_class = TaskForm
    template_name = "tasks/task_form.html"

    def test_func(self):
        task = self.get_object()

        return (
            self.request.user.is_staff
            or task.owner_id == self.request.user.id
        )

    def handle_no_permission(self):
        messages.error(
            self.request,
            "You do not have permission to edit that task.",
        )

        return redirect("task_list")


# -------------------------
# Delete Task
# -------------------------

class TaskDeleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    DeleteView,
):
    model = Task
    template_name = "tasks/task_confirm_delete.html"
    success_url = reverse_lazy("task_list")

    def test_func(self):
        task = self.get_object()

        return (
            self.request.user.is_staff
            or task.owner_id == self.request.user.id
        )

    def handle_no_permission(self):
        messages.error(
            self.request,
            "You do not have permission to delete that task.",
        )

        return redirect("task_list")

    def form_valid(self, form):
        messages.success(
            self.request,
            "Task deleted successfully.",
        )

        return super().form_valid(form)


# -------------------------
# Staff Report
# -------------------------

class StaffOnlyReportView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    View,
):

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        messages.error(
            self.request,
            "Staff access only.",
        )

        return redirect("task_list")

    def get(self, request):
        tasks = Task.objects.select_related(
            "owner",
            "category",
        ).all()

        return render(
            request,
            "tasks/staff_report.html",
            {"tasks": tasks},
        )