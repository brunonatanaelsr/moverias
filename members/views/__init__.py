
from django.views.generic import ListView, CreateView, DetailView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages

from members.models import Beneficiary
from members.forms import BeneficiaryForm

class BeneficiaryListView(LoginRequiredMixin, ListView):
    model = Beneficiary
    template_name = 'members/beneficiary_list.html'
    context_object_name = 'beneficiaries'
    
    def get_queryset(self):
        return Beneficiary.objects.all().order_by('-created_at')

class BeneficiaryCreateView(LoginRequiredMixin, CreateView):
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'members/beneficiary_form.html'
    success_url = reverse_lazy('members:list')

    def form_valid(self, form):
        messages.success(self.request, 'Beneficiária cadastrada com sucesso!')
        return super().form_valid(form)

class BeneficiaryDetailView(LoginRequiredMixin, DetailView):
    model = Beneficiary
    template_name = 'members/beneficiary_detail.html'
    context_object_name = 'beneficiary'

class BeneficiaryUpdateView(LoginRequiredMixin, UpdateView):
    model = Beneficiary
    form_class = BeneficiaryForm
    template_name = 'members/beneficiary_form.html'
    success_url = reverse_lazy('members:list')

    def form_valid(self, form):
        messages.success(self.request, 'Beneficiária atualizada com sucesso!')
        return super().form_valid(form)

class BeneficiaryDeleteView(LoginRequiredMixin, DeleteView):
    model = Beneficiary
    template_name = 'members/beneficiary_confirm_delete.html'
    success_url = reverse_lazy('members:list')

class BeneficiaryDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'members/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_beneficiaries'] = Beneficiary.objects.count()
        context['active_beneficiaries'] = Beneficiary.objects.filter(is_active=True).count()
        return context
