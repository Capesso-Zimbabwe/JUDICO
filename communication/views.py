from django.shortcuts import render

def communication_dashboard(request):
    return render(request, 'communication/dashboard.html')

def message_list(request):
    return render(request, 'communication/messages.html')

def message_create(request):
    return render(request, 'communication/message_create.html')

def notification_list(request):
    return render(request, 'communication/notifications.html')

def communication_settings(request):
    return render(request, 'communication/settings.html')

# Create your views here.
