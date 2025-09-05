"""apibase URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from apirest import views


urlpatterns = [
path('', views.health_check),  # Root path for health check
path('health/', views.health_check),
path('lists/', views.restric.as_view()),
path('ocr/', views.ocr2.as_view()),
path('ocr-raw/', views.ocrRaw.as_view()),
path('batch-ocr-raw/', views.BatchOCRRawView.as_view()),
path('upload/', views.FileUploadView.as_view()),
path('textract-id/', views.TextractIDAnalysisView.as_view()),
path('textract-general/', views.TextractGeneralAnalysisView.as_view()),
path('face/', views.Compare3.as_view()),
path('admin/', admin.site.urls),
path('login/', views.login),
]
