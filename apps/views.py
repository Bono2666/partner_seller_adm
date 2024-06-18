from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import connection, IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.forms.models import modelformset_factory
from apps.forms import *
from apps.mail import send_email
from apps.models import *
from authentication.decorators import role_required
from tablib import Dataset
from django.utils import timezone
import xlwt
from django.http import HttpResponse
import xlsxwriter
from django.db.models import Sum
from django.db.models import Max
from django.db.models import Min
from . import host
from reportlab.pdfgen import canvas
from django.http import FileResponse
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import landscape, A4
from django.db.models import Count
from PyPDF2 import PdfMerger
from django.conf import settings
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.utils.text import Truncator
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from crum import get_current_user


@login_required(login_url='/login/')
def home(request):
    context = {
        'segment': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
    }
    return render(request, 'home/index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, email, position_name FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id")
        users = cursor.fetchall()

    context = {
        'data': users,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/user_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_add(request):
    position = Position.objects.all()
    if request.POST:
        form = FormUser(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if not settings.DEBUG and form.instance.signature:
                user = User.objects.get(user_id=form.instance.user_id)
                my_file = user.signature
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)

            return HttpResponseRedirect(reverse('user-view', args=[form.instance.user_id, ]))
        else:
            message = form.errors
            context = {
                'form': form,
                'position': position,
                'segment': 'user',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/user_add.html', context)
    else:
        form = FormUser()
        context = {
            'form': form,
            'position': position,
            'segment': 'user',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/user_add.html', context)


# View User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_view(request, _id):
    users = User.objects.get(user_id=_id)
    auth = Auth.objects.filter(user_id=_id)
    area = AreaUser.objects.filter(user_id=_id)
    form = FormUserView(instance=users)
    position = Position.objects.all()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_menu.menu_id, menu_name, q_auth.menu_id FROM apps_menu LEFT JOIN (SELECT * FROM apps_auth WHERE user_id = '" + str(_id) + "') AS q_auth ON apps_menu.menu_id = q_auth.menu_id WHERE q_auth.menu_id IS NULL")
        menu = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_areasales.area_id, area_name, q_area.area_id FROM apps_areasales LEFT JOIN (SELECT * FROM apps_areauser WHERE user_id = '" + str(_id) + "') AS q_area ON apps_areasales.area_id = q_area.area_id WHERE q_area.area_id IS NULL")
        item_area = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in menu:
            if str(i[0]) in check:
                try:
                    auth = Auth(user_id=_id, menu_id=i[0])
                    auth.save()
                except IntegrityError:
                    continue
            else:
                Auth.objects.filter(user_id=_id, menu_id=i[0]).delete()

        return HttpResponseRedirect(reverse('user-view', args=[_id, ]))

    context = {
        'form': form,
        'formAuth': form,
        'data': users,
        'auth': auth,
        'menu': menu,
        'area': area,
        'item_area': item_area,
        'positions': position,
        'segment': 'user',
        'group_segment': 'master',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_view.html', context)


# View User Area
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_area_view(request, _id):
    users = User.objects.get(user_id=_id)
    auth = Auth.objects.filter(user_id=_id)
    area = AreaUser.objects.filter(user_id=_id)
    form = FormUserView(instance=users)
    position = Position.objects.all()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_menu.menu_id, menu_name, q_auth.menu_id FROM apps_menu LEFT JOIN (SELECT * FROM apps_auth WHERE user_id = '" + str(_id) + "') AS q_auth ON apps_menu.menu_id = q_auth.menu_id WHERE q_auth.menu_id IS NULL")
        menu = cursor.fetchall()
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_areasales.area_id, area_name, q_area.area_id FROM apps_areasales LEFT JOIN (SELECT * FROM apps_areauser WHERE user_id = '" + str(_id) + "') AS q_area ON apps_areasales.area_id = q_area.area_id WHERE q_area.area_id IS NULL")
        item_area = cursor.fetchall()

    if request.POST:
        area_check = request.POST.getlist('area[]')
        for i in item_area:
            if str(i[0]) in area_check:
                try:
                    area = AreaUser(user_id=_id, area_id=i[0])
                    area.save()
                except IntegrityError:
                    continue
            else:
                AreaUser.objects.filter(user_id=_id, area_id=i[0]).delete()

        return HttpResponseRedirect(reverse('user-area-view', args=[_id, ]))

    context = {
        'form': form,
        'formAuth': form,
        'data': users,
        'auth': auth,
        'menu': menu,
        'area': area,
        'item_area': item_area,
        'positions': position,
        'segment': 'user',
        'group_segment': 'master',
        'tab': 'area',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_view.html', context)


# Update Auth
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def auth_update(request, _id, _menu):
    auth = Auth.objects.get(user=_id, menu=_menu)

    if request.POST:
        auth.add = 1 if request.POST.get('add') else 0
        auth.edit = 1 if request.POST.get('edit') else 0
        auth.delete = 1 if request.POST.get('delete') else 0
        auth.save()

        return HttpResponseRedirect(reverse('user-view', args=[_id, ]))

    return render(request, 'home/user_view.html')


# Delete Auth
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def auth_delete(request, _id, _menu):
    auth = Auth.objects.filter(user=_id, menu=_menu)

    auth.delete()
    return HttpResponseRedirect(reverse('user-view', args=[_id, ]))


# Delete AreaUser
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def area_user_delete(request, _id, _area):
    area = AreaUser.objects.filter(user=_id, area=_area)

    area.delete()
    return HttpResponseRedirect(reverse('user-area-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def remove_signature(request, _id):
    users = User.objects.get(user_id=_id)
    users.signature = None
    users.save()
    return HttpResponseRedirect(reverse('user-view', args=[_id, ]))


# Update User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_update(request, _id):
    users = User.objects.get(user_id=_id)
    position = Position.objects.all()
    auth = Auth.objects.filter(user_id=_id)
    area = AreaUser.objects.filter(user_id=_id)

    if request.POST:
        form = FormUserUpdate(request.POST, request.FILES, instance=users)
        if form.is_valid():
            form.save()
            if not settings.DEBUG and users.signature:
                my_file = users.signature
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)
            return HttpResponseRedirect(reverse('user-view', args=[_id, ]))
    else:
        form = FormUserUpdate(instance=users)

    message = form.errors
    context = {
        'form': form,
        'data': users,
        'positions': position,
        'auth': auth,
        'area': area,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'update',
        'tab': 'auth',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_view.html', context)


# Delete User
@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def user_delete(request, _id):
    users = User.objects.get(user_id=_id)

    users.delete()
    return HttpResponseRedirect(reverse('user-index'))


@login_required(login_url='/login/')
def change_password(request):
    if request.POST:
        form = FormChangePassword(data=request.POST, user=request.user)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return HttpResponseRedirect(reverse('home'))
    else:
        form = FormChangePassword(user=request.user)

    message = form.errors
    context = {
        'form': form,
        'data': request.user,
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
    }
    return render(request, 'home/user_change_password.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='USER')
def set_password(request, _id):
    users = User.objects.get(user_id=_id)
    if request.POST:
        form = FormSetPassword(data=request.POST, user=users)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return HttpResponseRedirect(reverse('user-view', args=[_id, ]))
    else:
        form = FormSetPassword(user=users)

    message = form.errors
    context = {
        'form': form,
        'data': users,
        'segment': 'user',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='USER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/user_set_password.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT distributor_id, distributor_name, sap_code FROM apps_distributor")
        distributors = cursor.fetchall()

    context = {
        'data': distributors,
        'segment': 'distributor',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/distributor_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_add(request):
    if request.POST:
        form = FormDistributor(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('distributor-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'distributor',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/distributor_add.html', context)
    else:
        form = FormDistributor()
        context = {
            'form': form,
            'segment': 'distributor',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/distributor_add.html', context)


# View Distributor
@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_view(request, _id):
    distributors = Distributor.objects.get(distributor_id=_id)
    form = FormDistributorView(instance=distributors)

    context = {
        'form': form,
        'data': distributors,
        'segment': 'distributor',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/distributor_view.html', context)


# Update Distributor
@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_update(request, _id):
    distributors = Distributor.objects.get(distributor_id=_id)
    if request.POST:
        form = FormDistributorUpdate(
            request.POST, request.FILES, instance=distributors)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('distributor-view', args=[_id, ]))
    else:
        form = FormDistributorUpdate(instance=distributors)

    message = form.errors
    context = {
        'form': form,
        'data': distributors,
        'segment': 'distributor',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='DISTRIBUTOR') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/distributor_view.html', context)


# Delete Distributor
@login_required(login_url='/login/')
@role_required(allowed_roles='DISTRIBUTOR')
def distributor_delete(request, _id):
    distributors = Distributor.objects.get(distributor_id=_id)

    distributors.delete()
    return HttpResponseRedirect(reverse('distributor-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT area_id, area_name, username FROM apps_areasales INNER JOIN apps_user ON apps_areasales.manager = apps_user.user_id")
        area_sales = cursor.fetchall()

    context = {
        'data': area_sales,
        'segment': 'area_sales',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/area_sales_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_add(request):
    manager = User.objects.filter(position_id='ASM')

    if request.POST:
        form = FormAreaSales(request.POST, request.FILES)

        if form.is_valid():
            new = form.save(commit=False)
            new.area_id = form.cleaned_data.get('area_id').replace(' ', '')
            new.form = host.url + 'order/new/' + new.area_id
            new.save()
            return HttpResponseRedirect(reverse('area-sales-view', args=[form.instance.area_id, ]))
        else:
            message = form.errors
            context = {
                'form': form,
                'manager': manager,
                'segment': 'area_sales',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/area_sales_add.html', context)
    else:
        form = FormAreaSales()
        message = form.errors

        context = {
            'form': form,
            'manager': manager,
            'segment': 'area_sales',
            'group_segment': 'master',
            'crud': 'add',
            'message': message,
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/area_sales_add.html', context)


# View Area Sales
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_view(request, _id):
    area_sales = AreaSales.objects.get(area_id=_id)
    form = FormAreaSalesView(instance=area_sales)
    managers = User.objects.filter(position_id='ASM')

    context = {
        'form': form,
        'data': area_sales,
        'managers': managers,
        'segment': 'area_sales',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/area_sales_view.html', context)


# Update Area Sales
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_update(request, _id):
    area_sales = AreaSales.objects.get(area_id=_id)
    managers = User.objects.filter(position_id='ASM')

    if request.POST:
        form = FormAreaSalesUpdate(
            request.POST, request.FILES, instance=area_sales)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('area-sales-view', args=[_id, ]))
    else:
        form = FormAreaSalesUpdate(instance=area_sales)

    message = form.errors
    context = {
        'form': form,
        'data': area_sales,
        'managers': managers,
        'segment': 'area_sales',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='AREA') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/area_sales_view.html', context)


# Delete Area Sales
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA')
def area_sales_delete(request, _id):
    area_sales = AreaSales.objects.get(area_id=_id)

    area_sales.delete()
    return HttpResponseRedirect(reverse('area-sales-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_areachannel.area_id, apps_areasales.area_name, apps_user.username FROM apps_areachannel INNER JOIN apps_areasales ON apps_areachannel.area_id = apps_areasales.area_id INNER JOIN apps_user ON apps_areasales.manager = apps_user.user_id")
        area_channels = cursor.fetchall()

    context = {
        'data': area_channels,
        'segment': 'area_channel',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='AREA-CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/area_channel_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_add(request):
    channel = Channel.objects.all()
    areas = AreaSales.objects.all()
    if request.POST:
        form = FormAreaChannel(request.POST, request.FILES)
        if form.is_valid():
            parent = form.save(commit=False)
            parent.save()
            for i in channel:
                child = AreaChannelDetail(
                    area=parent, channel=i, status=0)
                child.save()
            return HttpResponseRedirect(reverse('area-channel-view', args=[form.instance.area_id, ]))
        else:
            message = form.errors
            context = {
                'form': form,
                'areas': areas,
                'segment': 'area_channel',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(
                    user_id=request.user.user_id, menu_id='AREA-CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/area_channel_add.html', context)
    else:
        form = FormAreaChannel()
        context = {
            'form': form,
            'areas': areas,
            'segment': 'area_channel',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(
                user_id=request.user.user_id, menu_id='AREA-CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/area_channel_add.html', context)


# View Area Channel
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_view(request, _id):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_areachannel.area_id, apps_areasales.area_name, apps_user.username FROM apps_areachannel INNER JOIN apps_areasales ON apps_areachannel.area_id = apps_areasales.area_id INNER JOIN apps_user ON apps_areasales.manager = apps_user.user_id WHERE apps_areachannel.area_id = '" + str(_id) + "'")
        area_channels = cursor.fetchone()

    detail = AreaChannelDetail.objects.filter(area=_id)

    context = {
        'data': area_channels,
        'detail': detail,
        'segment': 'area_channel',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='AREA-CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/area_channel_view.html', context)


# Delete Area Channel
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_delete(request, _id):
    area_channels = AreaChannel.objects.get(area_id=_id)

    area_channels.delete()
    return HttpResponseRedirect(reverse('area-channel-index'))


# Update Area Channel Detail
@login_required(login_url='/login/')
@role_required(allowed_roles='AREA-CHANNEL')
def area_channel_detail_update(request, _id, _channel):
    area_channels = AreaChannelDetail.objects.get(area=_id, channel=_channel)

    if request.POST:
        area_channels.status = 1 if request.POST.get('status') else 0
        area_channels.save()

        return HttpResponseRedirect(reverse('area-channel-view', args=[_id, ]))

    return render(request, 'home/area_channel_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_add(request):
    if request.POST:
        form = FormPosition(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('position-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'position',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/position_add.html', context)
    else:
        form = FormPosition()
        context = {
            'form': form,
            'segment': 'position',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/position_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT position_id, position_name FROM apps_position")
        positions = cursor.fetchall()

    context = {
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/position_index.html', context)


# Update Position
@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_update(request, _id):
    positions = Position.objects.get(position_id=_id)
    if request.POST:
        form = FormPositionUpdate(
            request.POST, request.FILES, instance=positions)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('position-view', args=[_id, ]))
    else:
        form = FormPositionUpdate(instance=positions)

    message = form.errors
    context = {
        'form': form,
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/position_view.html', context)


# Delete Position
@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_delete(request, _id):
    positions = Position.objects.get(position_id=_id)

    positions.delete()
    return HttpResponseRedirect(reverse('position-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='POSITION')
def position_view(request, _id):
    positions = Position.objects.get(position_id=_id)
    form = FormPositionView(instance=positions)

    context = {
        'form': form,
        'data': positions,
        'segment': 'position',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='POSITION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/position_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_add(request):
    if request.POST:
        form = FormMenu(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('menu-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'menu',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/menu_add.html', context)
    else:
        form = FormMenu()
        context = {
            'form': form,
            'segment': 'menu',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/menu_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT menu_id, menu_name, menu_remark FROM apps_menu")
        menus = cursor.fetchall()

    context = {
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/menu_index.html', context)


# Update Menu
@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_update(request, _id):
    menus = Menu.objects.get(menu_id=_id)
    if request.POST:
        form = FormMenuUpdate(request.POST, request.FILES, instance=menus)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('menu-view', args=[_id, ]))
    else:
        form = FormMenuUpdate(instance=menus)

    message = form.errors
    context = {
        'form': form,
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/menu_view.html', context)


# Delete Menu
@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_delete(request, _id):
    menus = Menu.objects.get(menu_id=_id)

    menus.delete()
    return HttpResponseRedirect(reverse('menu-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='MENU')
def menu_view(request, _id):
    menus = Menu.objects.get(menu_id=_id)
    form = FormMenuView(instance=menus)

    context = {
        'form': form,
        'data': menus,
        'segment': 'menu',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='MENU') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/menu_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_add(request):
    if request.POST:
        form = FormChannel(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('channel-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'channel',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/channel_add.html', context)
    else:
        form = FormChannel()
        context = {
            'form': form,
            'segment': 'channel',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/channel_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_index(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT channel_id, channel_name FROM apps_channel")
        channels = cursor.fetchall()

    context = {
        'data': channels,
        'segment': 'channel',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/channel_index.html', context)


# Update Channel
@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_update(request, _id):
    channels = Channel.objects.get(channel_id=_id)
    if request.POST:
        form = FormChannelUpdate(
            request.POST, request.FILES, instance=channels)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('channel-view', args=[_id, ]))
    else:
        form = FormChannelUpdate(instance=channels)

    message = form.errors
    context = {
        'form': form,
        'data': channels,
        'segment': 'channel',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/channel_view.html', context)


# Delete Channel
@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_delete(request, _id):
    channels = Channel.objects.get(channel_id=_id)

    channels.delete()
    return HttpResponseRedirect(reverse('channel-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CHANNEL')
def channel_view(request, _id):
    channels = Channel.objects.get(channel_id=_id)
    form = FormChannelView(instance=channels)

    context = {
        'form': form,
        'data': channels,
        'segment': 'channel',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CHANNEL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/channel_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_index(request):
    cuisines = Cuisine.objects.all()

    context = {
        'data': cuisines,
        'segment': 'cuisine',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cuisine_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_add(request):
    if request.POST:
        form = FormCuisine(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('cuisine-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'cuisine',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/cuisine_add.html', context)
    else:
        form = FormCuisine()
        context = {
            'form': form,
            'segment': 'cuisine',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/cuisine_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_view(request, _id):
    cuisines = Cuisine.objects.get(cuisine_id=_id)
    form = FormCuisineView(instance=cuisines)

    context = {
        'form': form,
        'data': cuisines,
        'segment': 'cuisine',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cuisine_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_update(request, _id):
    cuisines = Cuisine.objects.get(cuisine_id=_id)
    if request.POST:
        form = FormCuisineUpdate(
            request.POST, request.FILES, instance=cuisines)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('cuisine-view', args=[_id, ]))
    else:
        form = FormCuisineUpdate(instance=cuisines)

    message = form.errors
    context = {
        'form': form,
        'data': cuisines,
        'segment': 'cuisine',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUISINE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cuisine_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUISINE')
def cuisine_delete(request, _id):
    cuisines = Cuisine.objects.get(cuisine_id=_id)

    cuisines.delete()
    return HttpResponseRedirect(reverse('cuisine-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_index(request):
    categories = Category.objects.all()

    context = {
        'data': categories,
        'segment': 'category',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/category_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_add(request):
    if request.POST:
        form = FormCategory(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('category-index'))
        else:
            message = form.errors
            context = {
                'form': form,
                'segment': 'category',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/category_add.html', context)
    else:
        form = FormCategory()
        context = {
            'form': form,
            'segment': 'category',
            'group_segment': 'master',
            'crud': 'add',
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/category_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_view(request, _id):
    categories = Category.objects.get(category_id=_id)
    form = FormCategoryView(instance=categories)

    context = {
        'form': form,
        'data': categories,
        'segment': 'category',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/category_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_update(request, _id):
    categories = Category.objects.get(category_id=_id)
    if request.POST:
        form = FormCategoryUpdate(
            request.POST, request.FILES, instance=categories)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('category-view', args=[_id, ]))
    else:
        form = FormCategoryUpdate(instance=categories)

    message = form.errors
    context = {
        'form': form,
        'data': categories,
        'segment': 'category',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CATEGORY') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/category_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CATEGORY')
def category_delete(request, _id):
    categories = Category.objects.get(category_id=_id)

    categories.delete()
    return HttpResponseRedirect(reverse('category-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_index(request):
    packages = Package.objects.all()

    context = {
        'data': packages,
        'segment': 'package',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/package_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_add(request):
    categories = Category.objects.all()
    if request.POST:
        form = FormPackage(request.POST, request.FILES)
        if form.is_valid():
            new = form.save(commit=False)
            new.category_id = request.POST.get('category')
            new.type = request.POST.get('type')
            new.save()
            return HttpResponseRedirect(reverse('package-view', args=[new.package_id, ]))
        else:
            message = form.errors
            context = {
                'form': form,
                'categories': categories,
                'segment': 'package',
                'group_segment': 'master',
                'crud': 'add',
                'message': message,
                'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
                'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
            }
            return render(request, 'home/package_add.html', context)
    else:
        form = FormPackage()
        message = form.errors
        context = {
            'form': form,
            'categories': categories,
            'segment': 'package',
            'group_segment': 'master',
            'crud': 'add',
            'message': message,
            'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
            'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
        }
        return render(request, 'home/package_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('main_cuisine[]')
        for i in main_cuisines:
            if str(i.cuisine_id) in check:
                try:
                    main_cuisine = MainCuisine(
                        package=packages, cuisine=i)
                    main_cuisine.save()
                except IntegrityError:
                    continue
            else:
                MainCuisine.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'main_cuisine',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_subcuisine_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('sub_cuisine[]')
        for i in sub_cuisines:
            if str(i.cuisine_id) in check:
                try:
                    sub_cuisine = SubCuisine(
                        package=packages, cuisine=i)
                    sub_cuisine.save()
                except IntegrityError:
                    continue
            else:
                SubCuisine.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-subcuisine-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'sub_cuisine',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine1_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine1[]')
        for i in side_cuisines1:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine1 = SideCuisine1(
                        package=packages, cuisine=i)
                    side_cuisine1.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine1.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine1-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine1',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine2_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine2[]')
        for i in side_cuisines2:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine2 = SideCuisine2(
                        package=packages, cuisine=i)
                    side_cuisine2.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine2.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine2-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine2',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine3_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine3[]')
        for i in side_cuisines3:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine3 = SideCuisine3(
                        package=packages, cuisine=i)
                    side_cuisine3.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine3.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine3-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine3',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine4_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine4[]')
        for i in side_cuisines4:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine4 = SideCuisine4(
                        package=packages, cuisine=i)
                    side_cuisine4.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine4.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine4-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine4',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine5_view(request, _id):
    packages = Package.objects.get(package_id=_id)
    packages.male_price = '{:,}'.format(packages.male_price)
    packages.female_price = '{:,}'.format(packages.female_price)
    form = FormPackageView(instance=packages)
    categories = Category.objects.all()
    selected_cuisine = MainCuisine.objects.filter(package_id=_id)
    selected_subcuisine = SubCuisine.objects.filter(package_id=_id)
    selected_sidecuisine1 = SideCuisine1.objects.filter(package_id=_id)
    selected_sidecuisine2 = SideCuisine2.objects.filter(package_id=_id)
    selected_sidecuisine3 = SideCuisine3.objects.filter(package_id=_id)
    selected_sidecuisine4 = SideCuisine4.objects.filter(package_id=_id)
    selected_sidecuisine5 = SideCuisine5.objects.filter(package_id=_id)
    main_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=MainCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    sub_cuisines = Cuisine.objects.all().exclude(
        cuisine_id__in=SubCuisine.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines1 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine1.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines2 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine2.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines3 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine3.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines4 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine4.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))
    side_cuisines5 = Cuisine.objects.all().exclude(
        cuisine_id__in=SideCuisine5.objects.filter(package_id=_id).values_list('cuisine_id', flat=True))

    if request.POST:
        check = request.POST.getlist('side_cuisine5[]')
        for i in side_cuisines5:
            if str(i.cuisine_id) in check:
                try:
                    side_cuisine5 = SideCuisine5(
                        package=packages, cuisine=i)
                    side_cuisine5.save()
                except IntegrityError:
                    continue
            else:
                SideCuisine5.objects.filter(
                    package_id=_id, cuisine_id=i.cuisine_id).delete()

        return HttpResponseRedirect(reverse('package-sidecuisine5-view', args=[_id, ]))

    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'selected_cuisine': selected_cuisine,
        'selected_subcuisine': selected_subcuisine,
        'selected_sidecuisine1': selected_sidecuisine1,
        'selected_sidecuisine2': selected_sidecuisine2,
        'selected_sidecuisine3': selected_sidecuisine3,
        'selected_sidecuisine4': selected_sidecuisine4,
        'selected_sidecuisine5': selected_sidecuisine5,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'segment': 'package',
        'group_segment': 'master',
        'tab': 'side_cuisine5',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_maincuisine_delete(request, _id, _cuisine):
    MainCuisine.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_subcuisine_delete(request, _id, _cuisine):
    SubCuisine.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine1_delete(request, _id, _cuisine):
    SideCuisine1.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine2_delete(request, _id, _cuisine):
    SideCuisine2.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine3_delete(request, _id, _cuisine):
    SideCuisine3.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine4_delete(request, _id, _cuisine):
    SideCuisine4.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_sidecuisine5_delete(request, _id, _cuisine):
    SideCuisine5.objects.filter(
        package_id=_id, cuisine_id=_cuisine).delete()
    return HttpResponseRedirect(reverse('package-view', args=[_id, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_update(request, _id):
    packages = Package.objects.get(package_id=_id)
    categories = Category.objects.all()
    if request.POST:
        form = FormPackageUpdate(
            request.POST, request.FILES, instance=packages)
        if form.is_valid():
            update = form.save(commit=False)
            update.category_id = request.POST.get('category')
            update.type = request.POST.get('type')
            update.male_price = request.POST.get('male_price')
            update.female_price = request.POST.get('female_price')
            update.save()
            return HttpResponseRedirect(reverse('package-view', args=[_id, ]))
    else:
        form = FormPackageUpdate(instance=packages)

    message = form.errors
    context = {
        'form': form,
        'data': packages,
        'categories': categories,
        'segment': 'package',
        'group_segment': 'master',
        'crud': 'update',
        'tab': 'main_cuisine',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='PACKAGE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/package_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='PACKAGE')
def package_delete(request, _id):
    packages = Package.objects.get(package_id=_id)

    packages.delete()
    return HttpResponseRedirect(reverse('package-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_index(request):
    periods = Closing.objects.all()

    context = {
        'data': periods,
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_add(request):
    if request.POST:
        form = FormClosing(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('closing-index'))
    else:
        last_month = (datetime.datetime(datetime.datetime.now(
        ).year, datetime.datetime.now().month, 1) - datetime.timedelta(days=1)).month
        last_year = (datetime.datetime(datetime.datetime.now(
        ).year, datetime.datetime.now().month, 1) - datetime.timedelta(days=1)).year

        form = FormClosing(initial={'year_closed': last_year, 'month_closed': last_month,
                           'year_open': datetime.datetime.now().year, 'month_open': datetime.datetime.now().month})

    context = {
        'form': form,
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_update(request, _id):
    period = Closing.objects.get(document=_id)

    if request.POST:
        form = FormClosingUpdate(request.POST, request.FILES, instance=period)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('closing-view', args=[_id, ]))
    else:
        form = FormClosingUpdate(instance=period)

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    context = {
        'form': form,
        'data': period,
        'years': YEAR_CHOICES,
        'months': MONTH_CHOICES,
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_delete(request, _id):
    periods = Closing.objects.get(document=_id)
    periods.delete()

    return HttpResponseRedirect(reverse('closing-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLOSING-PERIOD')
def closing_view(request, _id):
    period = Closing.objects.get(document=_id)
    form = FormClosingView(instance=period)

    YEAR_CHOICES = []
    for r in range((datetime.datetime.now().year-1), (datetime.datetime.now().year+2)):
        YEAR_CHOICES.append(str(r))

    MONTH_CHOICES = []
    for r in range(1, 13):
        MONTH_CHOICES.append(str(r))

    context = {
        'data': period,
        'form': form,
        'years': YEAR_CHOICES,
        'months': MONTH_CHOICES,
        'segment': 'closing_period',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLOSING-PERIOD') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/closing_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_index(request):
    divisions = Division.objects.all()

    context = {
        'data': divisions,
        'segment': 'division',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DIVISION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/division_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_add(request):
    if request.POST:
        form = FormDivision(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('division-index'))
    else:
        form = FormDivision()

    context = {
        'form': form,
        'segment': 'division',
        'group_segment': 'master',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DIVISION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/division_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_update(request, _id):
    division = Division.objects.get(division_id=_id)

    if request.POST:
        form = FormDivisionUpdate(
            request.POST, request.FILES, instance=division)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('division-index'))
    else:
        form = FormDivisionUpdate(instance=division)

    context = {
        'form': form,
        'data': division,
        'segment': 'division',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DIVISION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/division_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_delete(request, _id):
    division = Division.objects.get(division_id=_id)
    division.delete()

    return HttpResponseRedirect(reverse('division-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='DIVISION')
def division_view(request, _id):
    division = Division.objects.get(division_id=_id)
    form = FormDivisionView(instance=division)

    context = {
        'data': division,
        'form': form,
        'segment': 'division',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='DIVISION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/division_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_index(request, _tab):
    claims = Claim.objects.all().order_by('-claim_id')
    drafts = Claim.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all
    draft_count = Claim.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').count
    pendings = Claim.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all
    pending_count = Claim.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').count
    inapprovals = Claim.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all
    inapproval_count = Claim.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').count
    opens = Claim.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all
    open_count = Claim.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').count

    context = {
        'data': claims,
        'drafts': drafts,
        'draft_count': draft_count,
        'pendings': pendings,
        'pending_count': pending_count,
        'inapprovals': inapprovals,
        'inapproval_count': inapproval_count,
        'opens': opens,
        'open_count': open_count,
        'tab': _tab,
        'segment': 'claim',
        'group_segment': 'claim',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_add(request, _area, _distributor, _program):
    selected_area = _area
    selected_distributor = _distributor
    selected_program = _program
    program = Program.objects.get(
        program_id=selected_program) if selected_program != '0' else None
    area = AreaUser.objects.filter(user_id=request.user.user_id).values_list(
        'area_id', 'area__area_name')
    distributors = Program.objects.filter(status='OPEN', area=selected_area).values_list(
        'proposal__budget__budget_distributor__distributor_id', 'proposal__budget__budget_distributor__distributor_name').distinct() if selected_area != '0' else None
    programs = Program.objects.filter(status='OPEN', deadline__gte=datetime.datetime.now().date(
    ), area=selected_area, proposal__budget__budget_distributor__distributor_id=selected_distributor, proposal__balance__gt=0).distinct() if selected_distributor != '0' else None
    proposal = Proposal.objects.get(
        proposal_id=program.proposal.proposal_id) if selected_program != '0' else None
    proposals = Proposal.objects.filter(
        status='OPEN', area=selected_area, balance__gt=0, budget__budget_distributor=selected_distributor).order_by('-proposal_id') if selected_distributor != '0' else None

    no_save = False
    add_prop = '0'
    message = ''
    difference = 0
    add_proposals = None

    if selected_area != '0' and selected_program != '0':
        approvers = ClaimMatrix.objects.filter(
            area_id=selected_area, channel=program.proposal.channel).order_by('sequence')
        if approvers.count() == 0 or approvers[0].limit > 0:
            no_save = True
            message = "No claim's approver found for this area and channel."

    try:
        _no = Claim.objects.all().order_by('seq_number').last()
    except Claim.DoesNotExist:
        _no = None
    if _no is None:
        format_no = '{:04d}'.format(1)
    else:
        format_no = '{:04d}'.format(_no.seq_number + 1)

    _id = 'CBS-4' + format_no + '/' + program.proposal.channel + '/' + selected_area + '/' + \
        program.proposal.budget.budget_distributor.distributor_id + '/' + \
        datetime.datetime.now().strftime('%m/%Y') if selected_program != '0' else 'CBS-4' + format_no + '/' + selected_area + '/0' + \
        '/' + datetime.datetime.now().strftime('%m/%Y')

    if request.POST:
        form = FormClaim(request.POST, request.FILES)
        difference = int(request.POST.get('amount')) - int(proposal.balance)
        if int(request.POST.get('amount')) > int(proposal.balance) and request.POST.get('additional_proposal') == '':
            add_prop = '1'
            message = 'Claim amount is greater than proposal balance.'
            add_proposals = Proposal.objects.filter(status='OPEN', area=selected_area, channel=proposal.channel, balance__gte=difference, budget__budget_distributor=selected_distributor).exclude(
                proposal_id=proposal.proposal_id).order_by('-proposal_id') if selected_program != '0' else None
        else:
            if form.is_valid():
                draft = form.save(commit=False)
                draft.program_id = selected_program
                draft.seq_number = _no.seq_number + 1 if _no else 1
                draft.entry_pos = request.user.position.position_id
                draft.total_claim = Decimal(request.POST.get('amount'))
                draft.amount = proposal.balance if request.POST.get(
                    'additional_proposal') else Decimal(request.POST.get('amount'))
                draft.additional_proposal_id = request.POST.get(
                    'additional_proposal')
                draft.additional_amount = difference if request.POST.get(
                    'additional_proposal') else 0
                draft.save()

                sum_amount = Claim.objects.filter(
                    proposal_id=draft.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount = Claim.objects.filter(additional_proposal=draft.proposal_id).exclude(
                    status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

                sum_amount2 = Claim.objects.filter(
                    proposal_id=draft.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount2 = Claim.objects.filter(additional_proposal=draft.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
                    Sum('additional_amount'))

                amount = sum_amount.get('amount__sum') if sum_amount.get(
                    'amount__sum') else 0
                additional_amount = sum_add_amount.get(
                    'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

                amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
                    'amount__sum') else 0
                additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
                    'additional_amount__sum') else 0

                proposal.proposal_claim = amount + additional_amount
                proposal.balance = proposal.total_cost - proposal.proposal_claim
                proposal.save()

                proposal2 = Proposal.objects.get(
                    proposal_id=draft.additional_proposal_id) if draft.additional_proposal else None
                if proposal2:
                    proposal2.proposal_claim = amount2 + additional_amount2
                    proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
                    proposal2.save()

                for approver in approvers:
                    release = ClaimRelease(
                        claim_id=draft.claim_id,
                        claim_approval_id=approver.approver_id,
                        claim_approval_name=approver.approver.username,
                        claim_approval_email=approver.approver.email,
                        claim_approval_position=approver.approver.position.position_id,
                        sequence=approver.sequence,
                        limit=approver.limit,
                        return_to=approver.return_to,
                        approve=approver.approve,
                        revise=approver.revise,
                        returned=approver.returned,
                        reject=approver.reject,
                        notif=approver.notif,
                        printed=approver.printed,
                        as_approved=approver.as_approved)
                    release.save()

                mail_sent = ClaimRelease.objects.filter(
                    claim_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
                if mail_sent[0] == False:
                    email = ClaimRelease.objects.filter(
                        claim_id=_id).order_by('sequence').values_list('claim_approval_email', flat=True)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT username FROM apps_claimrelease INNER JOIN apps_user ON apps_claimrelease.claim_approval_id = apps_user.user_id WHERE claim_id = '" + str(_id) + "' AND claim_approval_status = 'N' ORDER BY sequence LIMIT 1")
                        approver = cursor.fetchone()

                    subject = 'Claim Approval'
                    msg = 'Dear ' + approver[0] + ',\n\nYou have a new claim to approve. Please check your claim release list.\n\n' + \
                        'Click this link to approve, revise, return or reject this claim.\n' + host.url + 'claim_release/view/' + str(_id) + '/0/' + \
                        '\n\nThank you.'
                    send_email(subject, msg, [email[0]])

                    # update mail sent to true
                    release = ClaimRelease.objects.filter(
                        claim_id=_id).order_by('sequence').first()
                    release.mail_sent = True
                    release.save()

                return HttpResponseRedirect(reverse('claim-index', args=['pending', ]))
    else:
        form = FormClaim(initial={'area': selected_area, 'claim_id': _id})

    msg = form.errors
    context = {
        'form': form,
        'area': area,
        'distributors': distributors,
        'program': program,
        'programs': programs,
        'proposals': proposals,
        'add_proposals': add_proposals,
        'selected_area': selected_area,
        'selected_distributor': selected_distributor,
        'selected_program': selected_program,
        'msg': msg,
        'message': message,
        'no_save': no_save,
        'add_prop': add_prop,
        'difference': difference,
        'segment': 'claim',
        'group_segment': 'claim',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CLAIM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_view(request, _tab, _id):
    claim = Claim.objects.get(claim_id=_id)
    form = FormClaimView(instance=claim)
    program = Program.objects.get(program_id=claim.program_id)

    highest_approval = ClaimRelease.objects.filter(
        claim_id=_id, limit__gt=claim.total_claim).aggregate(Min('sequence')) if ClaimRelease.objects.filter(claim_id=_id, limit__gt=claim.total_claim).count() > 0 else ClaimRelease.objects.filter(claim_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = ClaimRelease.objects.filter(
            claim_id=_id, sequence__lt=highest_sequence).order_by('sequence')
    else:
        approval = ClaimRelease.objects.filter(
            claim_id=_id).order_by('sequence')

    context = {
        'data': claim,
        'form': form,
        'tab': _tab,
        'program': program,
        'approval': approval,
        'status': claim.status,
        'segment': 'claim',
        'group_segment': 'claim',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CLAIM') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/claim_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_update(request, _tab, _id):
    claim = Claim.objects.get(claim_id=_id)
    proposals = Proposal.objects.filter(
        status='OPEN', area=claim.area, balance__gt=0, budget__budget_distributor=claim.proposal.budget.budget_distributor).order_by('-proposal_id')
    program = Program.objects.get(program_id=claim.program_id)
    proposal = Proposal.objects.get(proposal_id=program.proposal.proposal_id)

    message = '0'
    add_prop = '0'
    difference = 0
    add_proposals = None
    add_prop_before = claim.additional_proposal
    amount_before = claim.amount

    if request.POST:
        form = FormClaimUpdate(request.POST, request.FILES, instance=claim)
        difference = int(request.POST.get('amount')) - \
            (int(proposal.balance) + int(claim.amount))
        if int(request.POST.get('amount')) > (int(program.proposal.balance) + int(claim.amount)) and request.POST.get('additional_proposal') == '':
            add_prop = '1'
            message = 'Claim amount is greater than proposal balance.'
            add_proposals = Proposal.objects.filter(status='OPEN', area=claim.area.area_id, channel=proposal.channel, balance__gte=difference, budget__budget_distributor=claim.proposal.budget.budget_distributor).exclude(
                proposal_id=proposal.proposal_id)
        else:
            if form.is_valid():
                draft = form.save(commit=False)
                draft.status = 'PENDING'
                draft.total_claim = Decimal(request.POST.get('amount'))
                draft.amount = proposal.balance + amount_before if request.POST.get(
                    'additional_proposal') else Decimal(request.POST.get('amount'))
                if int(request.POST.get('amount')) > (int(proposal.balance) + int(amount_before)):
                    draft.additional_proposal = request.POST.get(
                        'additional_proposal')
                else:
                    draft.additional_proposal = None
                draft.additional_amount = difference if request.POST.get(
                    'additional_proposal') else 0
                draft.save()

                sum_amount = Claim.objects.filter(
                    proposal_id=draft.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount = Claim.objects.filter(additional_proposal=draft.proposal_id).exclude(
                    status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

                sum_amount2 = Claim.objects.filter(
                    proposal_id=draft.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount2 = Claim.objects.filter(additional_proposal=draft.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
                    Sum('additional_amount'))

                amount = sum_amount.get('amount__sum') if sum_amount.get(
                    'amount__sum') else 0
                additional_amount = sum_add_amount.get(
                    'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

                amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
                    'amount__sum') else 0
                additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
                    'additional_amount__sum') else 0

                proposal.proposal_claim = amount + additional_amount
                proposal.balance = proposal.total_cost - proposal.proposal_claim
                proposal.save()

                proposal2 = Proposal.objects.get(
                    proposal_id=draft.additional_proposal) if draft.additional_proposal else None
                if proposal2:
                    proposal2.proposal_claim = amount2 + additional_amount2
                    proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
                    proposal2.save()
                else:
                    proposal3 = Proposal.objects.get(
                        proposal_id=add_prop_before) if add_prop_before else None
                    if proposal3:
                        proposal3.proposal_claim = amount2 + additional_amount2
                        proposal3.balance = proposal3.total_cost - proposal3.proposal_claim
                        proposal3.save()

                mail_sent = ClaimRelease.objects.filter(
                    claim_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
                if mail_sent[0] == False:
                    email = ClaimRelease.objects.filter(
                        claim_id=_id).order_by('sequence').values_list('claim_approval_email', flat=True)
                    with connection.cursor() as cursor:
                        cursor.execute(
                            "SELECT username FROM apps_claimrelease INNER JOIN apps_user ON apps_claimrelease.claim_approval_id = apps_user.user_id WHERE claim_id = '" + str(_id) + "' AND claim_approval_status = 'N' ORDER BY sequence LIMIT 1")
                        approver = cursor.fetchone()

                    subject = 'Claim Approval'
                    msg = 'Dear ' + approver[0] + ',\n\nYou have a new claim to approve. Please check your claim release list.\n\n' + \
                        'Click this link to approve, revise, return or reject this claim.\n' + host.url + 'claim_release/view/' + str(_id) + '/0/' + \
                        '\n\nThank you.'
                    send_email(subject, msg, [email[0]])

                    # update mail sent to true
                    release = ClaimRelease.objects.filter(
                        claim_id=_id).order_by('sequence').first()
                    release.mail_sent = True
                    release.save()

                return HttpResponseRedirect(reverse('claim-view', args=[_tab, _id]))
    else:
        form = FormClaimUpdate(instance=claim)

    err = form.errors
    context = {
        'form': form,
        'data': claim,
        'program': program,
        'proposals': proposals,
        'add_proposals': add_proposals,
        'add_prop': add_prop,
        'difference': difference,
        'tab': _tab,
        'message': message,
        'err': err,
        'segment': 'claim',
        'group_segment': 'claim',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLAIM') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_delete(request, _tab, _id):
    claim = Claim.objects.get(claim_id=_id)
    proposal = Proposal.objects.get(proposal_id=claim.proposal.proposal_id)
    claim.delete()

    sum_amount = Claim.objects.filter(
        proposal_id=claim.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
    sum_add_amount = Claim.objects.filter(additional_proposal=claim.proposal_id).exclude(
        status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

    sum_amount2 = Claim.objects.filter(
        proposal_id=claim.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
    sum_add_amount2 = Claim.objects.filter(additional_proposal=claim.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
        Sum('additional_amount'))

    amount = sum_amount.get('amount__sum') if sum_amount.get(
        'amount__sum') else 0
    additional_amount = sum_add_amount.get(
        'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

    amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
        'amount__sum') else 0
    additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
        'additional_amount__sum') else 0

    proposal.proposal_claim = amount + additional_amount
    proposal.balance = proposal.total_cost - proposal.proposal_claim
    proposal.save()

    proposal2 = Proposal.objects.get(
        proposal_id=claim.additional_proposal) if claim.additional_proposal else None
    if proposal2:
        proposal2.proposal_claim = amount2 + additional_amount2
        proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
        proposal2.save()

    return HttpResponseRedirect(reverse('claim-index', args=[_tab, ]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_claim.claim_id, apps_claim.claim_date, apps_distributor.distributor_name, apps_proposal.channel, apps_claim.total_claim, apps_claim.status, apps_claimrelease.sequence FROM apps_distributor INNER JOIN apps_budget ON apps_distributor.distributor_id = apps_budget.budget_distributor_id INNER JOIN apps_proposal ON apps_budget.budget_id = apps_proposal.budget_id INNER JOIN apps_claim ON apps_proposal.proposal_id = apps_claim.proposal_id INNER JOIN apps_claimrelease ON apps_claim.claim_id = apps_claimrelease.claim_id INNER JOIN (SELECT claim_id, MIN(sequence) AS seq FROM apps_claimrelease WHERE claim_approval_status = 'N' GROUP BY claim_id ORDER BY sequence ASC) AS q_group ON apps_claimrelease.claim_id = q_group.claim_id AND apps_claimrelease.sequence = q_group.seq WHERE (apps_claim.status = 'PENDING' OR apps_claim.status = 'IN APPROVAL') AND apps_claimrelease.claim_approval_id = '" + str(request.user.user_id) + "'")
        release = cursor.fetchall()

    context = {
        'data': release,
        'segment': 'claim_release',
        'group_segment': 'claim',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/claim_release_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_view(request, _id, _is_revise):
    claim = Claim.objects.get(claim_id=_id)
    form = FormClaimView(instance=claim)
    approved = ClaimRelease.objects.get(
        claim_id=_id, claim_approval_id=request.user.user_id).claim_approval_status
    program = Program.objects.get(program_id=claim.program_id)

    context = {
        'form': form,
        'data': claim,
        'approved': approved,
        'program': program,
        'is_revise': _is_revise,
        'status': claim.status,
        'segment': 'claim_release',
        'group_segment': 'claim',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
        'btn_release': ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id),
    }
    return render(request, 'home/claim_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_update(request, _id):
    claim = Claim.objects.get(claim_id=_id)
    program = Program.objects.get(program_id=claim.program_id)
    proposal = Proposal.objects.get(proposal_id=claim.proposal.proposal_id)
    proposals = Proposal.objects.filter(
        status='OPEN', area=claim.area, balance__gt=0, budget__budget_distributor=claim.proposal.budget.budget_distributor).order_by('-proposal_id')
    message = '0'
    add_prop = '0'
    difference = 0
    add_proposals = None
    add_prop_before = claim.additional_proposal
    amount_before = claim.amount
    _invoice = claim.invoice
    _invoice_date = claim.invoice_date
    _due_date = claim.due_date
    _amount = claim.amount
    _remarks = claim.remarks
    _additional_proposal = claim.additional_proposal
    _additional_amount = claim.additional_amount

    if request.POST:
        form = FormClaimUpdate(
            request.POST, request.FILES, instance=claim)
        difference = int(request.POST.get('amount')) - \
            (int(proposal.balance) + int(claim.amount))
        if int(request.POST.get('amount')) > (int(proposal.balance) + int(claim.amount)) and request.POST.get('additional_proposal') == '':
            add_prop = '1'
            message = 'Claim amount is greater than proposal balance.'
            add_proposals = Proposal.objects.filter(status='OPEN', area=claim.area.area_id, channel=proposal.channel, balance__gte=difference, budget__budget_distributor=claim.proposal.budget.budget_distributor).exclude(
                proposal_id=proposal.proposal_id).order_by('-proposal_id')
        else:
            if form.is_valid():
                parent = form.save(commit=False)
                invoice = _invoice if form.cleaned_data['invoice'] != _invoice else None
                invoice_date = _invoice_date if form.cleaned_data[
                    'invoice_date'] != _invoice_date else None
                due_date = _due_date if form.cleaned_data['due_date'] != _due_date else None
                claim_amount = _amount if form.cleaned_data['amount'] != _amount else None
                remarks = _remarks if form.cleaned_data['remarks'] != _remarks else None
                additional_proposal = _additional_proposal if request.POST.get(
                    'additional_proposal') != _additional_proposal else None
                add_amount = _additional_amount if request.POST.get(
                    'additional_amount') != _additional_amount else None
                parent.total_claim = Decimal(request.POST.get('amount'))
                parent.amount = proposal.balance + amount_before if request.POST.get(
                    'additional_proposal') else Decimal(request.POST.get('amount'))
                if int(request.POST.get('amount')) > (int(proposal.balance) + int(amount_before)):
                    parent.additional_proposal_id = request.POST.get(
                        'additional_proposal')
                else:
                    parent.additional_proposal_id = None
                parent.additional_amount = difference if request.POST.get(
                    'additional_proposal') else 0
                parent.save()

                sum_amount = Claim.objects.filter(
                    proposal_id=parent.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount = Claim.objects.filter(additional_proposal=parent.proposal_id).exclude(
                    status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

                sum_amount2 = Claim.objects.filter(
                    proposal_id=parent.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
                sum_add_amount2 = Claim.objects.filter(additional_proposal=parent.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
                    Sum('additional_amount'))

                amount = sum_amount.get('amount__sum') if sum_amount.get(
                    'amount__sum') else 0
                additional_amount = sum_add_amount.get(
                    'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

                amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
                    'amount__sum') else 0
                additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
                    'additional_amount__sum') else 0

                proposal.proposal_claim = amount + additional_amount
                proposal.balance = proposal.total_cost - proposal.proposal_claim
                proposal.save()

                proposal2 = Proposal.objects.get(
                    proposal_id=parent.additional_proposal) if parent.additional_proposal else None
                if proposal2:
                    proposal2.proposal_claim = amount2 + additional_amount2
                    proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
                    proposal2.save()
                else:
                    proposal3 = Proposal.objects.get(
                        proposal_id=add_prop_before) if add_prop_before else None
                    if proposal3:
                        proposal3.proposal_claim = amount2 + additional_amount2
                        proposal3.balance = proposal3.total_cost - proposal3.proposal_claim
                        proposal3.save()

                recipients = []

                release = ClaimRelease.objects.get(
                    claim_id=_id, claim_approval_id=request.user.user_id)
                release.revise_note = request.POST.get('revise_note')
                release.save()

                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.entry_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
                    entry_mail = cursor.fetchone()
                    if entry_mail:
                        recipients.append(entry_mail[1])

                    cursor.execute(
                        "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.update_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
                    update_mail = cursor.fetchone()
                    if update_mail:
                        recipients.append(update_mail[1])

                    cursor.execute(
                        "SELECT claim_id, claim_approval_email FROM apps_claimrelease WHERE claim_id = '" + str(_id) + "' AND claim_approval_status = 'Y'")
                    approver_mail = cursor.fetchall()
                    for mail in approver_mail:
                        recipients.append(mail[1])

                subject = 'Claim Revised'
                msg = 'Dear All,\n\nThe following is revised claim for Claim No. ' + \
                    str(_id) + ':\n'
                if invoice:
                    msg += '\nBEFORE\n'
                    msg += 'Invoice: ' + str(invoice) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Invoice: ' + \
                        form.cleaned_data['invoice'] + '\n'

                if invoice_date:
                    msg += '\nBEFORE\n'
                    msg += 'Invoice Date: ' + \
                        invoice_date.strftime('%d %b %Y') + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Invoice Date: ' + \
                        form.cleaned_data['invoice_date'].strftime(
                            '%d %b %Y') + '\n'

                if due_date:
                    msg += '\nBEFORE\n'
                    msg += 'Due Date: ' + \
                        due_date.strftime('%d %b %Y') + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Due Date: ' + \
                        form.cleaned_data['due_date'].strftime(
                            '%d %b %Y') + '\n'

                if claim_amount:
                    msg += '\nBEFORE\n'
                    msg += 'Amount: ' + str(claim_amount) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Amount: ' + \
                        str(form.cleaned_data['amount']) + '\n'

                if remarks:
                    msg += '\nBEFORE\n'
                    msg += 'Remarks: ' + str(remarks) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Remarks: ' + \
                        form.cleaned_data['remarks'] + '\n'

                if additional_proposal:
                    msg += '\nBEFORE\n'
                    msg += 'Additional Proposal: ' + \
                        str(additional_proposal) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Additional Proposal: ' + \
                        request.POST.get('additional_proposal') + '\n'

                if add_amount:
                    msg += '\nBEFORE\n'
                    msg += 'Additional Amount: ' + \
                        str(add_amount) + '\n'
                    msg += '\nAFTER\n'
                    msg += 'Additional Amount: ' + \
                        request.POST.get('additional_amount') + '\n'

                msg += '\nNote: ' + \
                    str(release.revise_note) + '\n\nClick the following link to view the claim.\n' + host.url + 'claim/view/inapproval/' + str(_id) + '/' + \
                    '\n\nThank you.'

                recipient_list = list(dict.fromkeys(recipients))
                send_email(subject, msg, recipient_list)

                return HttpResponseRedirect(reverse('claim-release-view', args=[_id, 0]))
    else:
        form = FormClaimUpdate(instance=claim)

    # msg = form.errors
    context = {
        'form': form,
        'data': claim,
        'program': program,
        'message': message,
        'add_prop': add_prop,
        'add_proposals': add_proposals,
        'proposals': proposals,
        'difference': difference,
        'segment': 'claim_release',
        'group_segment': 'claim',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id,
                                menu_id='CLAIM-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_approve(request, _id):
    claim = Claim.objects.get(claim_id=_id)
    release = ClaimRelease.objects.get(
        claim_id=_id, claim_approval_id=request.user.user_id)
    release.claim_approval_status = 'Y'
    release.claim_approval_date = timezone.now()
    release.save()

    highest_approval = ClaimRelease.objects.filter(
        claim_id=_id, limit__gt=claim.total_claim).aggregate(Min('sequence')) if ClaimRelease.objects.filter(claim_id=_id, limit__gt=claim.total_claim).count() > 0 else ClaimRelease.objects.filter(claim_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = ClaimRelease.objects.filter(
            claim_id=_id, sequence__lt=highest_sequence).order_by('sequence').last()
    else:
        approval = ClaimRelease.objects.filter(
            claim_id=_id).order_by('sequence').last()

    if release.sequence == approval.sequence:
        claim.status = 'OPEN'

        recipients = []

        maker = claim.entry_by
        maker_mail = User.objects.get(user_id=maker).email
        recipients.append(maker_mail)

        approvers = ClaimRelease.objects.filter(
            claim_id=_id, notif=True, claim_approval_status='Y')
        for i in approvers:
            recipients.append(i.claim_approval_email)

        subject = 'Claim Approved'
        msg = 'Dear All,\n\nClaim No. ' + str(_id) + ' has been approved.\n\nClick the following link to view the claim.\n' + host.url + 'claim/view/open/' + str(_id) + \
            '\n\nThank you.'
        recipient_list = list(dict.fromkeys(recipients))
        send_email(subject, msg, recipient_list)
    else:
        claim.status = 'IN APPROVAL'

        email = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='N').order_by(
            'sequence').values_list('claim_approval_email', flat=True)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT claim_approval_name FROM apps_claimrelease WHERE claim_id = '" + str(_id) + "' AND claim_approval_status = 'N' ORDER BY sequence LIMIT 1")
            approver = cursor.fetchone()

        subject = 'Claim Approval'
        msg = 'Dear ' + approver[0] + ',\n\nYou have a new claim to approve. Please check your claim release list.\n\n' + \
            'Click this link to approve, revise, return or reject this claim.\n' + host.url + 'claim_release/view/' + str(_id) + '/0/' + \
            '\n\nThank you.'
        send_email(subject, msg, [email[0]])

    claim.save()

    return HttpResponseRedirect(reverse('claim-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_return(request, _id):
    recipients = []
    draft = False

    try:
        return_to = ClaimRelease.objects.get(
            claim_id=_id, return_to=True, sequence__lt=ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id).sequence)

        if return_to:
            approvers = ClaimRelease.objects.filter(
                claim_id=_id, sequence__gte=ClaimRelease.objects.get(claim_id=_id, return_to=True).sequence, sequence__lt=ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id).sequence)
    except ClaimRelease.DoesNotExist:
        approvers = ClaimRelease.objects.filter(
            claim_id=_id, sequence__lte=ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id).sequence)
        draft = True

    for i in approvers:
        recipients.append(i.claim_approval_email)
        i.claim_approval_status = 'N'
        i.claim_approval_date = None
        i.revise_note = ''
        i.return_note = ''
        i.reject_note = ''
        i.mail_sent = False
        i.save()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.entry_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.update_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = ClaimRelease.objects.get(
        claim_id=_id, claim_approval_id=request.user.user_id)
    note.return_note = request.POST.get('return_note')
    note.save()

    subject = 'Claim Returned'
    msg = 'Dear All,\n\nClaim No. ' + str(_id) + ' has been returned.\n\nNote: ' + \
        str(note.return_note) + \
        '\n\nClick the following link to revise the claim.\n'

    if draft:
        claim = Claim.objects.get(claim_id=_id)
        claim.status = 'DRAFT'
        claim.save()
        msg += host.url + 'claim/view/pending/' + str(_id) + \
            '\n\nThank you.'
    else:
        msg += host.url + 'claim_release/view/' + \
            str(_id) + '/0/\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('claim-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-RELEASE')
def claim_release_reject(request, _id):
    claim = Claim.objects.get(claim_id=_id)
    proposal = Proposal.objects.get(proposal_id=claim.proposal.proposal_id)
    recipients = []

    try:
        approvers = ClaimRelease.objects.filter(
            claim_id=_id, sequence__lt=ClaimRelease.objects.get(claim_id=_id, claim_approval_id=request.user.user_id).sequence)
    except ClaimRelease.DoesNotExist:
        pass

    for i in approvers:
        recipients.append(i.claim_approval_email)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.entry_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT claim_id, email FROM apps_claim INNER JOIN apps_user ON apps_claim.update_by = apps_user.user_id WHERE claim_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = ClaimRelease.objects.get(
        claim_id=_id, claim_approval_id=request.user.user_id)
    note.reject_note = request.POST.get('reject_note')
    note.save()

    subject = 'Claim Rejected'
    msg = 'Dear All,\n\nClaim No. ' + str(_id) + ' has been rejected.\n\nNote: ' + \
        str(note.reject_note) + \
        '\n\nClick the following link to see the claim.\n'

    claim = Claim.objects.get(claim_id=_id)
    claim.status = 'REJECTED'
    claim.save()

    sum_amount = Claim.objects.filter(
        proposal_id=claim.proposal_id).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
    sum_add_amount = Claim.objects.filter(additional_proposal=claim.proposal_id).exclude(
        status__in=['REJECTED', 'DRAFT']).aggregate(Sum('additional_amount'))

    sum_amount2 = Claim.objects.filter(
        proposal_id=claim.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(Sum('amount'))
    sum_add_amount2 = Claim.objects.filter(additional_proposal=claim.additional_proposal).exclude(status__in=['REJECTED', 'DRAFT']).aggregate(
        Sum('additional_amount'))

    amount = sum_amount.get('amount__sum') if sum_amount.get(
        'amount__sum') else 0
    additional_amount = sum_add_amount.get(
        'additional_amount__sum') if sum_add_amount.get('additional_amount__sum') else 0

    amount2 = sum_amount2.get('amount__sum') if sum_amount2.get(
        'amount__sum') else 0
    additional_amount2 = sum_add_amount2.get('additional_amount__sum') if sum_add_amount2.get(
        'additional_amount__sum') else 0

    proposal.proposal_claim = amount + additional_amount
    proposal.balance = proposal.total_cost - proposal.proposal_claim
    proposal.save()

    proposal2 = Proposal.objects.get(
        proposal_id=claim.additional_proposal) if claim.additional_proposal else None
    if proposal2:
        proposal2.proposal_claim = amount2 + additional_amount2
        proposal2.balance = proposal2.total_cost - proposal2.proposal_claim
        proposal2.save()

    msg += host.url + 'claim/view/reject/' + str(_id) + \
        '\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('claim-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM')
def claim_print(request, _id):
    claim = Claim.objects.get(claim_id=_id)
    claim_id = _id.replace('/', '-')

    # Create a new PDF file with landscape orientation
    filename = 'claim_' + claim_id + '.pdf'
    pdf_file = canvas.Canvas(filename, pagesize=landscape(A4))

    # Set the font and font size
    pdf_file.setFont('Helvetica-Bold', 11)

    # Add logo in the center of the page
    logo_path = 'https://aqiqahon.sahabataqiqah.co.id/apps/static/img/logo.png'
    logo_width = 60
    logo_height = 60
    page_width = landscape(A4)
    logo_x = (page_width[0] - logo_width) / 2
    pdf_file.drawImage(logo_path, logo_x, 515,
                       width=logo_width, height=logo_height)

    # Add title in the center of page width
    title = 'DEBIT NOTE'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 11)
    title_x = (page_width[0] - title_width) / 2
    pdf_file.setFont('Helvetica-Bold', 11)
    pdf_file.drawString(title_x, 500, title)

    # Write the claim details
    y = 450
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Claim No.')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.claim_id))
    pdf_file.setFont('Helvetica-Bold', 8)
    y -= 10
    pdf_file.drawString(25, y, 'Claim Date')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, claim.claim_date.strftime('%d %b %Y'))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Proposal No.')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.proposal.proposal_id))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Program Name')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.proposal.program_name))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Invoice No.')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.invoice))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Invoice Date')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, claim.invoice_date.strftime('%d %b %Y'))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Due Date')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, claim.due_date.strftime('%d %b %Y'))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Amount')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, '{:,}'.format(claim.total_claim))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Additional Proposal')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(
        claim.additional_proposal if claim.additional_proposal else '-'))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Additional Amount')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, '{:,}'.format(
        claim.additional_amount) if claim.additional_amount else '-')
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Tax')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, '{:,}'.format(claim.tax))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Total Amount')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, '{:,}'.format(claim.total))
    y -= 10
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.drawString(25, y, 'Remarks')
    pdf_file.drawString(150, y, ': ')
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(160, y, str(claim.remarks))

    y -= 50
    col_width = (page_width[0] - 50) / 11
    approver = ClaimRelease.objects.filter(
        claim_id=_id, claim_approval_status='Y', printed=True).order_by('sequence')
    verificator = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='verificator', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='verificator', printed=True).exists() else 0
    area_approver = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='area_approver', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='area_approver', printed=True).exists() else 0
    checker = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='checker', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='checker', printed=True).exists() else 0
    ho_approver = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='ho_approver', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='ho_approver', printed=True).exists() else 0
    validator = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='validator', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='validator', printed=True).exists() else 0
    finalizer = ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='finalizer', printed=True).aggregate(id=Count(
        'id')) if ClaimRelease.objects.filter(claim_id=_id, claim_approval_status='Y', as_approved='finalizer', printed=True).exists() else 0

    verificator_count = verificator['id'] if verificator else 0
    area_approver_count = area_approver['id'] if area_approver else 0
    checker_count = checker['id'] if checker else 0
    ho_approver_count = ho_approver['id'] if ho_approver else 0
    validator_count = validator['id'] if validator else 0
    finalizer_count = finalizer['id'] if finalizer else 0

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25, y-5, col_width, 15, stroke=True)
    title = 'Prepared By'
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + col_width, y-5,
                  col_width * verificator_count, 15, stroke=True)
    title = 'Verified By' if verificator_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + col_width + \
        ((col_width * verificator_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + 1)), y-5,
                  col_width * area_approver_count, 15, stroke=True)
    title = 'Approved By' if area_approver_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + 1)) + \
        ((col_width * area_approver_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + area_approver_count + 1)),
                  y-5, col_width * checker_count, 15, stroke=True)
    title = 'Checked By' if checker_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + area_approver_count + 1)
                    ) + ((col_width * checker_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + area_approver_count +
                  checker_count + 1)), y-5, col_width * ho_approver_count, 15, stroke=True)
    title = 'Approved By' if ho_approver_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + area_approver_count +
                    checker_count + 1)) + ((col_width * ho_approver_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + area_approver_count + checker_count +
                  ho_approver_count + 1)), y-5, col_width * validator_count, 15, stroke=True)
    title = 'Validated By' if validator_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + area_approver_count + checker_count +
                    ho_approver_count + 1)) + ((col_width * validator_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont('Helvetica', 8)
    pdf_file.rect(25 + (col_width * (verificator_count + area_approver_count + checker_count +
                  ho_approver_count + validator_count + 1)), y-5, col_width * finalizer_count, 15, stroke=True)
    title = 'Approved By' if finalizer_count > 0 else ''
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width * (verificator_count + area_approver_count + checker_count +
                    ho_approver_count + validator_count + 1)) + ((col_width * finalizer_count) - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(25, y - 55, col_width, 50, stroke=True)
    sign_path = User.objects.get(user_id=claim.entry_by).signature.path if User.objects.get(
        user_id=claim.entry_by).signature else ''
    if sign_path:
        pdf_file.drawImage(sign_path, 30, y - 50,
                           width=col_width - 10, height=40)
    else:
        pass
    pdf_file.rect(25, y - 70, col_width, 15, stroke=True)
    title = claim.entry_pos
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    title_x = 25 + (col_width - title_width) / 2
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(title_x, y - 65, title)
    pdf_file.rect(25, y - 85, col_width, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    title = 'Date: ' + claim.entry_date.strftime('%d/%m/%Y')
    title_width = pdf_file.stringWidth(title, "Helvetica", 8)
    title_x = 25 + (col_width - title_width) / 2
    pdf_file.drawString(title_x, y - 80, title)

    for i in range(1, approver.count() + 1):
        pdf_file.rect(25 + (col_width * i), y - 55, col_width, 50, stroke=True)
        if approver:
            sign_path = User.objects.get(user_id=approver[i - 1].claim_approval_id).signature.path if User.objects.get(
                user_id=approver[i - 1].claim_approval_id).signature else ''
            if sign_path:
                pdf_file.drawImage(sign_path, 30 + (col_width * i), y - 50,
                                   width=col_width - 10, height=40)
            else:
                pass
            pdf_file.rect(25 + (col_width * i), y - 70,
                          col_width, 15, stroke=True)
            title = approver[i - 1].claim_approval_position
            title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
            title_x = 25 + (col_width * i) + (col_width - title_width) / 2
            pdf_file.setFont("Helvetica-Bold", 8)
            pdf_file.drawString(title_x, y - 65, title)
            pdf_file.rect(25 + (col_width * i), y - 85,
                          col_width, 15, stroke=True)
            pdf_file.setFont("Helvetica", 8)
            title = 'Date: ' + \
                approver[i - 1].claim_approval_date.strftime('%d/%m/%Y')
            title_width = pdf_file.stringWidth(title, "Helvetica", 8)
            title_x = 25 + (col_width * i) + (col_width - title_width) / 2
            pdf_file.drawString(title_x, y - 80, title)
        else:
            pass

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-ARCHIVE')
def claim_archive_index(request):
    rejects = Claim.objects.filter(status='REJECTED', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-claim_id').all

    context = {
        'rejects': rejects,
        'segment': 'claim_archive',
        'group_segment': 'claim',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CLAIM-ARCHIVE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_archive.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-APPROVAL')
def claim_matrix_index(request):
    areas = AreaSales.objects.all()

    context = {
        'data': areas,
        'segment': 'claim_matrix',
        'group_segment': 'approval',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_matrix_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-APPROVAL')
def claim_matrix_view(request, _id, _channel):
    area = AreaSales.objects.get(area_id=_id)
    channels = AreaChannelDetail.objects.filter(area_id=_id, status=1)
    approvers = ClaimMatrix.objects.filter(area_id=_id, channel_id=_channel)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, position_name, q_claimmatrix.approver_id FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id LEFT JOIN (SELECT * FROM apps_claimmatrix WHERE area_id = '" + str(_id) + "' AND channel_id = '" + str(_channel) + "') AS q_claimmatrix ON apps_user.user_id = q_claimmatrix.approver_id WHERE q_claimmatrix.approver_id IS NULL")
        users = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in users:
            if str(i[0]) in check:
                try:
                    approver = ClaimMatrix(
                        area_id=_id, channel_id=_channel, approver_id=i[0])
                    approver.save()
                except IntegrityError:
                    continue
            else:
                ClaimMatrix.objects.filter(
                    area_id=_id, channel_id=_channel, approver_id=i[0]).delete()

        return HttpResponseRedirect(reverse('claim-matrix-view', args=[_id, _channel]))

    context = {
        'data': area,
        'channels': channels,
        'users': users,
        'approvers': approvers,
        'channel': _channel,
        'segment': 'claim_matrix',
        'group_segment': 'approval',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CLAIM-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/claim_matrix_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-APPROVAL')
def claim_matrix_update(request, _id, _channel, _approver):
    approvers = ClaimMatrix.objects.get(
        area=_id, channel_id=_channel, approver_id=_approver)

    if request.POST:
        approvers.sequence = int(request.POST.get('sequence'))
        approvers.limit = int(request.POST.get('limit'))
        approvers.return_to = True if request.POST.get('return') else False
        approvers.approve = True if request.POST.get('approve') else False
        approvers.revise = True if request.POST.get('revise') else False
        approvers.returned = True if request.POST.get('returned') else False
        approvers.reject = True if request.POST.get('reject') else False
        approvers.notif = True if request.POST.get('notif') else False
        approvers.printed = True if request.POST.get('printed') else False
        approvers.as_approved = request.POST.get('as_approved')
        approvers.save()

        return HttpResponseRedirect(reverse('claim-matrix-view', args=[_id, _channel]))

    return render(request, 'home/claim_matrix_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='CLAIM-APPROVAL')
def claim_matrix_delete(request, _id, _channel, _arg):
    approvers = ClaimMatrix.objects.get(
        area=_id, channel_id=_channel, approver_id=_arg)
    approvers.delete()

    return HttpResponseRedirect(reverse('claim-matrix-view', args=[_id, _channel]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_index(request, _tab):
    cl = CL.objects.all()
    drafts = CL.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cl_id').all
    draft_count = CL.objects.filter(status='DRAFT', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).count
    pendings = CL.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cl_id').all
    pending_count = CL.objects.filter(status='PENDING', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).count
    inapprovals = CL.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cl_id').all
    inapproval_count = CL.objects.filter(status='IN APPROVAL', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).count
    opens = CL.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cl_id').all
    open_count = CL.objects.filter(status='OPEN', area__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).count

    context = {
        'data': cl,
        'drafts': drafts,
        'draft_count': draft_count,
        'pendings': pendings,
        'pending_count': pending_count,
        'inapprovals': inapprovals,
        'inapproval_count': inapproval_count,
        'opens': opens,
        'open_count': open_count,
        'tab': _tab,
        'segment': 'cl',
        'group_segment': 'cl',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_add(request, _area, _distributor):
    selected_area = _area
    selected_distributor = _distributor
    area = AreaUser.objects.filter(user_id=request.user.user_id).values_list(
        'area_id', 'area__area_name')
    distributors = Claim.objects.filter(status='OPEN', area=selected_area).values_list(
        'proposal__budget__budget_distributor', 'proposal__budget__budget_distributor__distributor_name').distinct() if selected_area != '0' else None

    no_save = False
    message = ''

    if selected_area != '0' and selected_distributor != '0':
        approvers = CLMatrix.objects.filter(
            area_id=selected_area).order_by('sequence')
        if approvers.count() == 0:
            no_save = True
            message = "No communication letter's approver found for this area."

    try:
        _no = CL.objects.all().order_by('seq_number').last()
    except CL.DoesNotExist:
        _no = None
    if _no is None:
        format_no = '{:04d}'.format(1)
    else:
        format_no = '{:04d}'.format(_no.seq_number + 1)

    _id = 'LBS-5' + format_no + '/' + selected_area + \
        '/' + selected_distributor + '/' + datetime.datetime.now().strftime('%m/%Y')

    if selected_area != '0' and selected_distributor != '0' and not no_save:
        parent = CL(cl_id=_id, cl_date=datetime.datetime.now(), area_id=selected_area,
                    distributor_id=selected_distributor, entry_pos=request.user.position.position_id, seq_number=_no.seq_number + 1 if _no else 1)
        parent.save()

        for i in approvers:
            _cl = CL.objects.get(cl_id=_id)
            release = CLRelease(
                cl_id=_cl,
                cl_approval_id=i.approver_id,
                cl_approval_name=i.approver.username,
                cl_approval_email=i.approver.email,
                cl_approval_position=i.approver.position.position_id,
                sequence=i.sequence,
                limit=i.limit,
                return_to=i.return_to,
                approve=i.approve,
                revise=i.revise,
                returned=i.returned,
                reject=i.reject,
                notif=i.notif,
                printed=i.printed,
                as_approved=i.as_approved)
            release.save()

        return HttpResponseRedirect(reverse('cl-view', args=['draft', _id]))

    context = {
        'selected_area': selected_area,
        'selected_distributor': selected_distributor,
        'area': area,
        'distributors': distributors,
        'no_save': no_save,
        'message': message,
        'segment': 'cl',
        'group_segment': 'cl',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_view(request, _tab, _id):
    cl = CL.objects.get(cl_id=_id)
    cl_detail = CLDetail.objects.filter(cl_id=_id)
    claim = Claim.objects.filter(status='OPEN', area_id=cl.area_id, proposal__budget__budget_distributor=cl.distributor_id).exclude(
        cldetail__claim_id__in=CLDetail.objects.all().values_list('claim_id', flat=True)).values_list('claim_id', 'remarks', 'cldetail__claim_id')

    highest_approval = CLRelease.objects.filter(
        cl_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = CLRelease.objects.filter(
            cl_id=_id, sequence__lt=highest_sequence).order_by('sequence')
    else:
        approval = CLRelease.objects.filter(cl_id=_id).order_by('sequence')

    if request.POST:
        check = request.POST.getlist('checks[]')
        _cl = CL.objects.get(cl_id=_id)
        for i in claim:
            if str(i[0]) in check:
                try:
                    detail = CLDetail(cl_id=_cl, claim_id=i[0])
                    detail.save()
                except IntegrityError:
                    continue
            else:
                CLDetail.objects.filter(cl_id=_id, claim_id=i[0]).delete()

        cl.status = 'PENDING'
        cl.save()

        mail_sent = CLRelease.objects.filter(
            cl_id=_id).order_by('sequence').values_list('mail_sent', flat=True)
        if mail_sent[0] == False:
            email = CLRelease.objects.filter(
                cl_id=_id).order_by('sequence').values_list('cl_approval_email', flat=True)
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT username FROM apps_clrelease INNER JOIN apps_user ON apps_clrelease.cl_approval_id = apps_user.user_id WHERE cl_id_id = '" + str(_id) + "' AND cl_approval_status = 'N' ORDER BY sequence LIMIT 1")
                approver = cursor.fetchone()

            subject = 'CL Approval'
            msg = 'Dear ' + approver[0] + ',\n\nYou have a new CL to approve. Please check your CL release list.\n\n' + \
                'Click this link to approve, revise, return or reject this CL.\n' + host.url + 'cl_release/view/' + str(_id) + '/0/' + \
                '\n\nThank you.'
            send_email(subject, msg, [email[0]])

            # update mail sent to true
            release = CLRelease.objects.filter(
                cl_id=_id).order_by('sequence').first()
            release.mail_sent = True
            release.save()

        return HttpResponseRedirect(reverse('cl-view', args=[_tab, _id]))

    context = {
        'data': cl,
        'cl_detail': cl_detail,
        'claim': claim,
        'tab': _tab,
        'approval': approval,
        'status': cl.status,
        'segment': 'cl',
        'group_segment': 'cl',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CL') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cl_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cldetail_delete(request, _tab, _id):
    detail = CLDetail.objects.get(id=_id)
    detail.delete()

    return HttpResponseRedirect(reverse('cl-view', args=[_tab, detail.cl_id_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cldetail_release_delete(request, _id):
    detail = CLDetail.objects.get(id=_id)
    detail.delete()

    return HttpResponseRedirect(reverse('cl-release-view', args=[detail.cl_id_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_delete(request, _tab, _id):
    cl = CL.objects.get(cl_id=_id)

    cl.delete()
    return HttpResponseRedirect(reverse('cl-index', args=[_tab]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_index(request):
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT apps_cl.cl_id, apps_cl.cl_date, apps_cl.area_id, apps_distributor.distributor_name, apps_cl.status, apps_clrelease.sequence FROM apps_distributor INNER JOIN apps_cl ON apps_distributor.distributor_id = apps_cl.distributor_id INNER JOIN apps_clrelease ON apps_cl.cl_id = apps_clrelease.cl_id_id INNER JOIN (SELECT cl_id_id, MIN(sequence) AS seq FROM apps_clrelease WHERE cl_approval_status = 'N' GROUP BY cl_id_id ORDER BY sequence ASC) AS q_group ON apps_clrelease.cl_id_id = q_group.cl_id_id AND apps_clrelease.sequence = q_group.seq WHERE (apps_cl.status = 'PENDING' OR apps_cl.status = 'IN APPROVAL') AND apps_clrelease.cl_approval_id = '" + str(request.user.user_id) + "'")
        release = cursor.fetchall()

    context = {
        'data': release,
        'segment': 'cl_release',
        'group_segment': 'cl',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cl_release_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_view(request, _id, _is_revise):
    cl = CL.objects.get(cl_id=_id)
    cl_detail = CLDetail.objects.filter(cl_id=_id)
    approved = CLRelease.objects.get(
        cl_id=_id, cl_approval_id=request.user.user_id).cl_approval_status
    claim = Claim.objects.filter(status='OPEN', area_id=cl.area_id, proposal__budget__budget_distributor=cl.distributor_id).exclude(
        cldetail__claim_id__in=CLDetail.objects.all().values_list('claim_id', flat=True)).values_list('claim_id', 'remarks', 'cldetail__claim_id')

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in claim:
            if str(i[0]) in check:
                try:
                    detail = CLDetail(cl_id=_id, claim_id=i[0])
                    detail.save()
                except IntegrityError:
                    continue
            else:
                CLDetail.objects.filter(cl_id=_id, claim_id=i[0]).delete()

        return HttpResponseRedirect(reverse('cl-release-view', args=[_id, 0]))

    context = {
        'data': cl,
        'cl_detail': cl_detail,
        'claim': claim,
        'approved': approved,
        'is_revise': _is_revise,
        'segment': 'cl_release',
        'group_segment': 'cl',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
        'btn_release': CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id) if not request.user.is_superuser else None,
    }
    return render(request, 'home/cl_release_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_update(request, _id):
    cl = CL.objects.get(cl_id=_id)
    cl_detail = CLDetail.objects.filter(cl_id=_id)
    claim = Claim.objects.filter(status='OPEN', area_id=cl.area_id, proposal__budget__budget_distributor=cl.distributor_id).exclude(
        cldetail__claim_id__in=CLDetail.objects.all().values_list('claim_id', flat=True)).values_list('claim_id', 'remarks', 'cldetail__claim_id')

    _add = ''
    _remove = ''

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in claim:
            if str(i[0]) in check:
                try:
                    detail = CLDetail(cl_id=_id, claim_id=i[0])
                    detail.save()
                    _add += i[0] + '\n'
                except IntegrityError:
                    continue
            else:
                CLDetail.objects.filter(cl_id=_id, claim_id=i[0]).delete()
                _remove += i[0] + '\n'

        recipients = []

        release = CLRelease.objects.get(
            cl_id=_id, cl_approval_id=request.user.user_id)
        release.revise_note = request.POST.get('revise_note')
        release.save()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.entry_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
            entry_mail = cursor.fetchone()
            if entry_mail:
                recipients.append(entry_mail[1])

            cursor.execute(
                "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.update_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
            update_mail = cursor.fetchone()
            if update_mail:
                recipients.append(update_mail[1])

            cursor.execute(
                "SELECT cl_id, cl_approval_email FROM apps_clrelease WHERE cl_id = '" + str(_id) + "' AND cl_approval_status = 'Y'")
            approver_mail = cursor.fetchall()
            for mail in approver_mail:
                recipients.append(mail[1])

        subject = 'CL Revised'
        msg = 'Dear All,\n\nThe following is revised CL for CL No. ' + \
            str(_id) + ':\n'
        msg += '\nCLAIM ADD:\n'
        msg += _add
        msg += '\nCLAIM REMOVE\n'
        msg += _remove

        msg += '\nNote: ' + \
            str(release.revise_note) + '\n\nClick the following link to view the CL.\n' + host.url + 'cl/view/inapproval/' + str(_id) + '/' + \
            '\n\nThank you.'

        recipient_list = list(dict.fromkeys(recipients))
        send_email(subject, msg, recipient_list)

        return HttpResponseRedirect(reverse('cl-release-view', args=[_id, 0]))

    context = {
        'data': cl,
        'cl_detail': cl_detail,
        'claim': claim,
        'segment': 'cl_release',
        'group_segment': 'cl',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CL-RELEASE') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_approve(request, _id):
    cl = CL.objects.get(cl_id=_id)
    release = CLRelease.objects.get(
        cl_id=_id, cl_approval_id=request.user.user_id)
    release.cl_approval_status = 'Y'
    release.cl_approval_date = timezone.now()
    release.save()

    highest_approval = CLRelease.objects.filter(
        cl_id=_id).aggregate(Max('sequence'))
    highest_sequence = highest_approval.get('sequence__min') if highest_approval.get(
        'sequence__min') else highest_approval.get('sequence__max') + 1
    if highest_sequence:
        approval = CLRelease.objects.filter(
            cl_id=_id, sequence__lt=highest_sequence).order_by('sequence').last()
    else:
        approval = CLRelease.objects.filter(
            cl_id=_id).order_by('sequence').last()

    if release.sequence == approval.sequence:
        cl.status = 'OPEN'

        recipients = []

        maker = cl.entry_by
        maker_mail = User.objects.get(user_id=maker).email
        recipients.append(maker_mail)

        approvers = CLRelease.objects.filter(
            cl_id=_id, notif=True, cl_approval_status='Y')
        for i in approvers:
            recipients.append(i.cl_approval_email)

        subject = 'CL Approved'
        msg = 'Dear All,\n\nCL No. ' + str(_id) + ' has been approved.\n\nClick the following link to view the CL.\n' + host.url + 'cl/view/open/' + str(_id) + \
            '\n\nThank you.'
        recipient_list = list(dict.fromkeys(recipients))
        send_email(subject, msg, recipient_list)
    else:
        cl.status = 'IN APPROVAL'

        email = CLRelease.objects.filter(cl_id=_id, cl_approval_status='N').order_by(
            'sequence').values_list('cl_approval_email', flat=True)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT cl_approval_name FROM apps_clrelease WHERE cl_id_id = '" + str(_id) + "' AND cl_approval_status = 'N' ORDER BY sequence LIMIT 1")
            approver = cursor.fetchone()

        subject = 'CL Approval'
        msg = 'Dear ' + approver[0] + ',\n\nYou have a new CL to approve. Please check your CL release list.\n\n' + \
            'Click this link to approve, revise, return or reject this CL.\n' + host.url + 'cl_release/view/' + str(_id) + '/0/' + \
            '\n\nThank you.'
        send_email(subject, msg, [email[0]])

    cl.save()

    return HttpResponseRedirect(reverse('cl-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_return(request, _id):
    recipients = []
    draft = False

    try:
        return_to = CLRelease.objects.get(
            cl_id=_id, return_to=True, sequence__lt=CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id).sequence)

        if return_to:
            approvers = CLRelease.objects.filter(
                cl_id=_id, sequence__gte=CLRelease.objects.get(cl_id=_id, return_to=True).sequence, sequence__lt=CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id).sequence)
    except CLRelease.DoesNotExist:
        approvers = CLRelease.objects.filter(
            claim_id=_id, sequence__lte=CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id).sequence)
        draft = True

    for i in approvers:
        recipients.append(i.claim_approval_email)
        i.claim_approval_status = 'N'
        i.claim_approval_date = None
        i.revise_note = ''
        i.return_note = ''
        i.reject_note = ''
        i.mail_sent = False
        i.save()

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.entry_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.update_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = CLRelease.objects.get(
        cl_id=_id, cl_approval_id=request.user.user_id)
    note.return_note = request.POST.get('return_note')
    note.save()

    subject = 'CL Returned'
    msg = 'Dear All,\n\nCL No. ' + str(_id) + ' has been returned.\n\nNote: ' + \
        str(note.return_note) + \
        '\n\nClick the following link to revise the CL.\n'

    if draft:
        cl = CL.objects.get(claim_id=_id)
        cl.status = 'DRAFT'
        cl.save()
        msg += host.url + 'cl/view/pending/' + str(_id) + \
            '\n\nThank you.'
    else:
        msg += host.url + 'cl_release/view/' + \
            str(_id) + '/0/\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('claim-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-RELEASE')
def cl_release_reject(request, _id):
    cl = CL.objects.get(cl_id=_id)
    recipients = []

    try:
        approvers = CLRelease.objects.filter(
            cl_id=_id, sequence__lt=CLRelease.objects.get(cl_id=_id, cl_approval_id=request.user.user_id).sequence)
    except CLRelease.DoesNotExist:
        pass

    for i in approvers:
        recipients.append(i.cl_approval_email)

    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.entry_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
        entry_mail = cursor.fetchone()
        if entry_mail:
            recipients.append(entry_mail[1])

        cursor.execute(
            "SELECT cl_id, email FROM apps_cl INNER JOIN apps_user ON apps_cl.update_by = apps_user.user_id WHERE cl_id = '" + str(_id) + "'")
        update_mail = cursor.fetchone()
        if update_mail:
            recipients.append(update_mail[1])

    note = CLRelease.objects.get(
        cl_id=_id, cl_approval_id=request.user.user_id)
    note.reject_note = request.POST.get('reject_note')
    note.save()

    cl = CL.objects.get(cl_id=_id)
    cl.status = 'REJECTED'
    cl.save()

    subject = 'CL Rejected'
    msg = 'Dear All,\n\nCL No. ' + str(_id) + ' has been rejected.\n\nNote: ' + \
        str(note.reject_note) + \
        '\n\nClick the following link to see the CL.\n'
    msg += host.url + 'cl/view/reject/' + str(_id) + \
        '\n\nThank you.'
    recipient_list = list(dict.fromkeys(recipients))
    send_email(subject, msg, recipient_list)

    return HttpResponseRedirect(reverse('cl-release-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-APPROVAL')
def cl_matrix_index(request):
    areas = AreaSales.objects.all()

    context = {
        'data': areas,
        'segment': 'cl_matrix',
        'group_segment': 'approval',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_matrix_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-APPROVAL')
def cl_matrix_view(request, _id):
    area = AreaSales.objects.get(area_id=_id)
    approvers = CLMatrix.objects.filter(area_id=_id)
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT user_id, username, position_name, q_clmatrix.approver_id FROM apps_user INNER JOIN apps_position ON apps_user.position_id = apps_position.position_id LEFT JOIN (SELECT * FROM apps_clmatrix WHERE area_id = '" + str(_id) + "') AS q_clmatrix ON apps_user.user_id = q_clmatrix.approver_id WHERE q_clmatrix.approver_id IS NULL")
        users = cursor.fetchall()

    if request.POST:
        check = request.POST.getlist('checks[]')
        for i in users:
            if str(i[0]) in check:
                try:
                    approver = CLMatrix(area_id=_id, approver_id=i[0])
                    approver.save()
                except IntegrityError:
                    continue
            else:
                CLMatrix.objects.filter(area_id=_id, approver_id=i[0]).delete()

        return HttpResponseRedirect(reverse('cl-matrix-view', args=[_id]))

    context = {
        'data': area,
        'users': users,
        'approvers': approvers,
        'segment': 'cl_matrix',
        'group_segment': 'approval',
        'tab': 'auth',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CL-APPROVAL') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/cl_matrix_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-APPROVAL')
def cl_matrix_update(request, _id, _approver):
    approvers = CLMatrix.objects.get(area=_id, approver_id=_approver)

    if request.POST:
        approvers.sequence = int(request.POST.get('sequence'))
        # approvers.limit = int(request.POST.get('limit'))
        approvers.return_to = True if request.POST.get('return') else False
        approvers.approve = True if request.POST.get('approve') else False
        approvers.revise = True if request.POST.get('revise') else False
        approvers.returned = True if request.POST.get('returned') else False
        approvers.reject = True if request.POST.get('reject') else False
        approvers.notif = True if request.POST.get('notif') else False
        approvers.printed = True if request.POST.get('printed') else False
        approvers.as_approved = request.POST.get('as_approved')
        approvers.save()

        return HttpResponseRedirect(reverse('cl-matrix-view', args=[_id]))

    return render(request, 'home/cl_matrix_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='CL-APPROVAL')
def cl_matrix_delete(request, _id, _arg):
    approvers = CLMatrix.objects.get(area=_id, approver_id=_arg)
    approvers.delete()

    return HttpResponseRedirect(reverse('cl-matrix-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CL')
def cl_print(request, _id):
    cl = CL.objects.get(cl_id=_id)
    cl_detail = CLDetail.objects.filter(cl_id=_id)
    detail_sum = Claim.objects.filter(
        claim_id__in=cl_detail.values_list('claim_id')).aggregate(total=Sum('total_claim'))
    approver = CLRelease.objects.filter(
        cl_id=_id, cl_approval_status='Y', printed=True).order_by('sequence')
    cl_id = _id.replace('/', '-')

    # Create a new PDF file with landscape orientation
    filename = 'CL-' + cl_id + '.pdf'
    pdf_file = canvas.Canvas(filename, pagesize=landscape(A4))

    # Set the font and font size
    pdf_file.setFont('Helvetica-Bold', 8)

    # Add logo in the center of the page
    logo_path = 'https://aqiqahon.sahabataqiqah.co.id/apps/static/img/logo.png'
    logo_width = 60
    logo_height = 60
    page_width = landscape(A4)
    logo_x = (page_width[0] - logo_width) / 2
    pdf_file.drawImage(logo_path, logo_x, 515,
                       width=logo_width, height=logo_height)

    # Add header
    y = 500
    pdf_file.drawString(25, y, 'Jakarta, ' + cl.cl_date.strftime('%d %B %Y'))
    pdf_file.drawRightString(800, y, 'No. ' + cl.cl_id)

    y -= 25
    pdf_file.drawString(25, y, 'Kepada Yth.')
    y -= 10
    pdf_file.drawString(25, y, cl.distributor.distributor_name)
    y -= 10
    pdf_file.drawString(25, y, 'Di tempat')

    y -= 25
    pdf_file.setFont('Helvetica', 8)
    pdf_file.drawString(25, y, 'Dengan hormat,')

    y -= 25
    pdf_file.drawString(25, y, 'Bersama ini kami sampaikan daftar program yang akan memotong Budget Selisih Margin PT. ABC PI di ' +
                        cl.distributor.distributor_name + ' sebagai berikut:')

    y -= 20
    pdf_file.setFont('Helvetica-Bold', 8)
    pdf_file.rect(25, y - 5, 25, 15, stroke=True)
    title = 'No.'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 25 + (25 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(50, y-5, 150, 15, stroke=True)
    title = 'No. Klaim'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 50 + (150 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(200, y-5, 225, 15, stroke=True)
    title = 'Deskripsi'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 200 + (225 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(425, y-5, 75, 15, stroke=True)
    title = 'Nilai Klaim'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 425 + (75 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(500, y-5, 150, 15, stroke=True)
    title = 'No. Surat Program'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 500 + (150 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.rect(650, y-5, 150, 15, stroke=True)
    title = 'No. Proposal'
    title_width = pdf_file.stringWidth(title, 'Helvetica-Bold', 8)
    title_x = 650 + (150 - title_width) / 2
    pdf_file.drawString(title_x, y, title)

    pdf_file.setFont("Helvetica", 8)
    n = 0
    for i in cl_detail:
        y -= 15
        n += 1
        pdf_file.rect(25, y - 5, 25, 15, stroke=True)
        title = str(n)
        title_width = pdf_file.stringWidth(title, 'Helvetica', 8)
        title_x = 25 + (25 - title_width) / 2
        pdf_file.drawString(title_x, y, title)
        pdf_file.rect(50, y - 5, 150, 15, stroke=True)
        pdf_file.drawString(55, y, i.claim_id)
        pdf_file.rect(200, y - 5, 225, 15, stroke=True)
        remarks = Truncator(i.claim.remarks).chars(55)
        pdf_file.drawString(205, y, remarks)
        pdf_file.rect(425, y - 5, 75, 15, stroke=True)
        pdf_file.drawRightString(495, y, "{:,}".format(i.claim.total_claim))
        pdf_file.rect(500, y - 5, 150, 15, stroke=True)
        pdf_file.drawString(505, y, i.claim.program_id)
        pdf_file.rect(650, y - 5, 150, 15, stroke=True)
        pdf_file.drawString(655, y, i.claim.proposal_id)

    y -= 15
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.rect(25, y - 5, 775, 15, stroke=True)
    pdf_file.drawRightString(420, y, 'TOTAL')
    pdf_file.drawRightString(495, y, "{:,}".format(detail_sum['total']))

    y -= 25
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(
        25, y, 'Demikian surat konfirmasi ini kami sampaikan. Atas perhatian dan kerjasamanya kami ucapkann terima kasih.')

    y -= 25
    pdf_file.drawString(25, y, 'Hormat Kami,')

    col_width = (page_width[0] - 50) / 11
    for i in range(1, approver.count() + 1):
        if approver:
            sign_path = User.objects.get(user_id=approver[i - 1].cl_approval_id).signature.path if User.objects.get(
                user_id=approver[i - 1].cl_approval_id).signature else ''
            pos = User.objects.get(
                user_id=approver[i - 1].cl_approval_id).position
            if sign_path:
                pdf_file.drawImage(sign_path, 25 + ((col_width * 2) * (i - 1)), y - 50,
                                   width=col_width - 10, height=40)
            else:
                pass

            pdf_file.setFont("Helvetica-Bold", 8)
            pdf_file.drawString(25 + ((col_width * 2) * (i - 1)),
                                y - 60, approver[i - 1].cl_approval_name)
            pdf_file.setFont("Helvetica", 8)
            pdf_file.drawString(25 + ((col_width * 2) * (i - 1)),
                                y - 70, str(pos))

    y -= 95
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(25, y, 'Cc : Finance Department')

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_index(request):
    regions = Region.objects.all()

    context = {
        'data': regions,
        'segment': 'region',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='REGION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/region_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_add(request):
    if request.POST:
        form = FormRegion(request.POST)
        if form.is_valid():
            region = form.save(commit=False)
            region.region_id = form.cleaned_data['region_id'].replace(' ', '')
            region.save()

            return HttpResponseRedirect(reverse('region-view', args=[region.region_id]))
    else:
        form = FormRegion()

    message = form.errors
    context = {
        'form': form,
        'segment': 'region',
        'group_segment': 'master',
        'crud': 'add',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='REGION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/region_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_view(request, _id):
    region = Region.objects.get(region_id=_id)
    form = FormRegionView(instance=region)
    details = RegionDetail.objects.filter(region_id=_id)
    areas = AreaSales.objects.exclude(regiondetail__region_id=_id).values_list(
        'area_id', 'area_name', 'regiondetail__region_id')

    if request.POST:
        check = request.POST.getlist('checks[]')
        for area in areas:
            if str(area[0]) in check:
                try:
                    detail = RegionDetail(region_id=_id, area_id=area[0])
                    detail.save()
                except IntegrityError:
                    continue
            else:
                RegionDetail.objects.filter(
                    region_id=_id, area_id=area[0]).delete()

    context = {
        'form': form,
        'data': region,
        'areas': areas,
        'detail': details,
        'segment': 'region',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='REGION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/region_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_update(request, _id):
    region = Region.objects.get(region_id=_id)
    detail = RegionDetail.objects.filter(region_id=_id)

    if request.POST:
        form = FormRegionUpdate(request.POST, instance=region)
        if form.is_valid():
            region = form.save(commit=False)
            region.save()

            return HttpResponseRedirect(reverse('region-view', args=[_id]))
    else:
        form = FormRegionUpdate(instance=region)

    message = form.errors
    context = {
        'form': form,
        'data': region,
        'detail': detail,
        'segment': 'region',
        'group_segment': 'master',
        'crud': 'update',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='REGION') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/region_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_delete(request, _id):
    region = Region.objects.get(region_id=_id)
    region.delete()

    return HttpResponseRedirect(reverse('region-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='REGION')
def region_detail_delete(request, _id, _area):
    detail = RegionDetail.objects.get(region_id=_id, area_id=_area)
    detail.delete()

    return HttpResponseRedirect(reverse('region-view', args=[_id]))


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_index(request):
    customers = Customer.objects.all()

    context = {
        'data': customers,
        'segment': 'customer',
        'group_segment': 'master',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CUSTOMER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/customer_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_add(request):
    if request.POST:
        form = FormCustomer(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.save()

            return HttpResponseRedirect(reverse('customer-view', args=[customer.customer_id, '0']))
    else:
        form = FormCustomer()

    message = form.errors
    context = {
        'form': form,
        'segment': 'customer',
        'group_segment': 'master',
        'crud': 'add',
        'message': message,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CUSTOMER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/customer_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_view(request, _id, _msg):
    customer = Customer.objects.get(customer_id=_id)
    form = FormCustomerView(instance=customer)
    form_detail = FormCustomerDetail(
        initial={'child_birth': datetime.date.today()})
    details = CustomerDetail.objects.filter(customer_id=_id)
    msg = _msg

    if request.POST:
        form_detail = FormCustomerDetail(request.POST)
        if form_detail.is_valid():
            try:
                detail = form_detail.save(commit=False)
                detail.customer_id = _id
                detail.child_sex = request.POST.get('child_sex')
                detail.save()
            except IntegrityError:
                msg = 'Nama anak sudah ada.'

            return HttpResponseRedirect(reverse('customer-view', args=[_id, msg]))

    context = {
        'form': form,
        'form_detail': form_detail,
        'data': customer,
        'details': details,
        'msg': msg,
        'segment': 'customer',
        'group_segment': 'master',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CUSTOMER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/customer_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_update(request, _id):
    customer = Customer.objects.get(customer_id=_id)

    if request.POST:
        form = FormCustomerUpdate(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.save()

            return HttpResponseRedirect(reverse('customer-view', args=[_id, '0']))
    else:
        form = FormCustomerUpdate(instance=customer)

    context = {
        'form': form,
        'data': customer,
        'msg': '0',
        'segment': 'customer',
        'group_segment': 'master',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list(
            'menu_id', flat=True),
        'btn': Auth.objects.get(
            user_id=request.user.user_id, menu_id='CUSTOMER') if not request.user.is_superuser else Auth.objects.all(),
    }
    return render(request, 'home/customer_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_delete(request, _id):
    customer = Customer.objects.get(customer_id=_id)
    customer.delete()

    return HttpResponseRedirect(reverse('customer-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_detail_update(request, _id, _child):
    detail = CustomerDetail.objects.get(id=_child)

    if request.POST:
        detail.child_name = request.POST.get('child_name')
        detail.child_birth = request.POST.get('child_birth')
        detail.child_sex = request.POST.get('child_sex')
        detail.child_father = request.POST.get('child_father')
        detail.child_mother = request.POST.get('child_mother')
        detail.save()

        return HttpResponseRedirect(reverse('customer-view', args=[_id, '0']))

    return render(request, 'home/customer_view.html')


@login_required(login_url='/login/')
@role_required(allowed_roles='CUSTOMER')
def customer_detail_delete(request, _id):
    detail = CustomerDetail.objects.get(id=_id)
    detail.delete()

    return HttpResponseRedirect(reverse('customer-view', args=[_id, '0']))


def order_add(request, _reg):
    num = _reg.split('/')[1] if '/' in _reg else '0'

    if num == '0':
        try:
            _no = Order.objects.filter(
                order_date__year=datetime.datetime.now().year).latest('seq_number')
        except Order.DoesNotExist:
            _no = None

        if _no is None:
            format_no = '{:05d}'.format(1)
            num = 1
        else:
            format_no = '{:05d}'.format(_no.seq_number + 1)
            _no.seq_number += 1
            _no.save()
            num = _no.seq_number

        _id = 'INV-1' + format_no + '/' + _reg.upper() + '/SA/' + str(datetime.datetime.now().strftime('%m')) + \
            '/' + str(datetime.datetime.now().year)

    if request.POST:
        form = FormOrder(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.regional_id = _reg.split('/')[0]
            order.seq_number = num
            order.save()

            return HttpResponseRedirect(reverse('order-child-add', args=[order.order_id, 0]))
    else:
        form = FormOrder(initial={'order_id': _id})

    msg = form.errors
    context = {
        'form': form,
        'crud': 'add',
        'reg': _reg+'/'+str(num),
        'msg': msg,
    }
    return render(request, 'home/order_add.html', context)


def order_update(request, _id):
    order = Order.objects.get(order_id=_id)

    if request.POST:
        form = FormOrderUpdate(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.save()

            child = OrderChild.objects.filter(order_id=_id)
            if child:
                return HttpResponseRedirect(reverse('order-child-update', args=[_id, child.first().id, 0]))
            else:
                return HttpResponseRedirect(reverse('order-child-add', args=[_id, 0]))
    else:
        form = FormOrderUpdate(instance=order)

    msg = form.errors

    context = {
        'form': form,
        'data': order,
        'msg': msg,
        'crud': 'update',
    }
    return render(request, 'home/order_update.html', context)


def order_child_add(request, _id, _add):
    try:
        last_child = OrderChild.objects.filter(order_id=_id).last()
    except OrderChild.DoesNotExist:
        last_child = None

    if request.POST:
        form = FormOrderChild(request.POST)
        if form.is_valid():
            child = form.save(commit=False)
            child.order_id = _id
            child.child_sex = request.POST.get('child_sex')
            child.save()

            package = OrderPackage.objects.filter(order_id=_id)
            if _add == 1:
                return HttpResponseRedirect(reverse('order-child-add', args=[_id, 0]))
            else:
                if package:
                    return HttpResponseRedirect(reverse('order-package-update', args=[_id, package[0].id, package[0].category_id, package[0].package_id, package[0].type, 0]))
                else:
                    return HttpResponseRedirect(reverse('order-package-add', args=[_id, '0', '0', '0', 0]))
    else:
        form = FormOrderChild(initial={'order': _id})

    msg = form.errors
    context = {
        'form': form,
        'crud': 'add',
        'last_child': last_child,
        'order_id': _id,
        'msg': msg,
    }
    return render(request, 'home/order_child_add.html', context)


def order_cs_child_add(request, _id):
    if request.POST:
        _child = OrderChild.objects.get(order_id=_id, child_name=request.POST.get('child_name')) if OrderChild.objects.filter(
            order_id=_id, child_name=request.POST.get('child_name')) else None
        if not _child:
            child = OrderChild(
                order_id=_id,
                child_name=request.POST.get('child_name'),
                child_birth=request.POST.get('child_birth'),
                child_sex=request.POST.get('child_sex'),
                child_father=request.POST.get('child_father'),
                child_mother=request.POST.get('child_mother'),
            )
            child.save()

            customer = Customer.objects.get(customer_phone=child.order.customer_phone) if Customer.objects.filter(
                customer_phone=child.order.customer_phone) else None
            if not customer:
                new_customer = Customer(
                    customer_phone=child.order.customer_phone,
                    customer_name=child.order.customer_name,
                    customer_phone2=child.order.customer_phone2,
                    customer_address=child.order.customer_address,
                    customer_email=child.order.customer_email,
                    customer_district=child.order.customer_district,
                    customer_city=child.order.customer_city,
                    customer_province=child.order.customer_province,
                )
                new_customer.save()

                children = OrderChild.objects.filter(order_id=_id)
                for i in children:
                    new_child = CustomerDetail(
                        customer_id=new_customer.customer_id,
                        child_name=i.child_name,
                        child_birth=i.child_birth,
                        child_sex=i.child_sex,
                        child_father=i.child_father,
                        child_mother=i.child_mother,
                    )
                    new_child.save()
            else:
                _child = CustomerDetail.objects.get(customer_id=customer.customer_id, child_name=child.child_name) if CustomerDetail.objects.filter(
                    customer_id=customer.customer_id, child_name=child.child_name) else None
                if not _child:
                    new_child = CustomerDetail(
                        customer_id=customer.customer_id,
                        child_name=request.POST.get('child_name'),
                        child_birth=request.POST.get('child_birth'),
                        child_sex=request.POST.get('child_sex'),
                        child_father=request.POST.get('child_father'),
                        child_mother=request.POST.get('child_mother'),
                    )
                    new_child.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_child_update(request, _id, _child, _add):
    child = OrderChild.objects.get(order_id=_id, id=_child)
    children = OrderChild.objects.filter(order_id=_id).order_by('id')

    first = False
    prev_id = 0

    first_child = OrderChild.objects.filter(order_id=_id).first()
    if first_child.id == _child:
        first = True

    for index, i in enumerate(children):
        if i.id == _child:
            n_child = index + 1

    for i in reversed(children):
        if i.id < _child:
            prev_id = i.id
            break

    if request.POST:
        form = FormOrderChildUpdate(request.POST, instance=child)
        if form.is_valid():
            child = form.save(commit=False)
            child.child_sex = request.POST.get('child_sex')
            child.save()

            last_child = OrderChild.objects.filter(order_id=_id).last()
            if _add == 1:
                return HttpResponseRedirect(reverse('order-child-add', args=[_id, 0]))
            else:
                if last_child.id == _child:
                    package = OrderPackage.objects.filter(order_id=_id)
                    if package:
                        return HttpResponseRedirect(reverse('order-package-update', args=[_id, package[0].id, package[0].category_id, package[0].package_id, package[0].type, 0]))
                    else:
                        return HttpResponseRedirect(reverse('order-package-add', args=[_id, '0', '0', '0', 0]))
                else:
                    for i in OrderChild.objects.filter(order_id=_id):
                        if i.id > _child:
                            return HttpResponseRedirect(reverse('order-child-update', args=[_id, i.id, 0]))
    else:
        form = FormOrderChildUpdate(instance=child)

    context = {
        'form': form,
        'data': child,
        'first_child': first,
        'n_child': n_child,
        'children': children,
        'prev_id': prev_id,
        'crud': 'update',
    }
    return render(request, 'home/order_child_update.html', context)


def order_child_cs_update(request, _id, _child):
    child = OrderChild.objects.get(order_id=_id, id=_child)

    if request.POST:
        child.child_name = request.POST.get('child_name')
        child.child_birth = request.POST.get('child_birth')
        child.child_sex = request.POST.get('child_sex')
        child.child_father = request.POST.get('child_father')
        child.child_mother = request.POST.get('child_mother')
        child.save()

        customer = Customer.objects.get(
            customer_phone=child.order.customer_phone) if Customer.objects.filter(customer_phone=child.order.customer_phone) else None
        if customer:
            detail = CustomerDetail.objects.get(customer_id=customer.customer_id, child_name=child.child_name) if CustomerDetail.objects.filter(
                customer_id=customer.customer_id, child_name=child.child_name) else None
            if detail:
                detail.child_birth = request.POST.get('child_birth')
                detail.child_name = request.POST.get('child_name')
                detail.child_sex = request.POST.get('child_sex')
                detail.child_father = request.POST.get('child_father')
                detail.child_mother = request.POST.get('child_mother')
                detail.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_child_delete(request, _id, _child):
    child = OrderChild.objects.get(order_id=_id, id=_child)
    child.delete()

    first = OrderChild.objects.filter(order_id=_id).first()

    return HttpResponseRedirect(reverse('order-child-update', args=[_id, first.id, 0]))


def order_child_cs_delete(request, _id, _child):
    child = OrderChild.objects.get(order_id=_id, id=_child)
    child.delete()

    customer = Customer.objects.get(customer_phone=child.order.customer_phone) if Customer.objects.filter(
        customer_phone=child.order.customer_phone) else None
    if customer:
        detail = CustomerDetail.objects.get(customer_id=customer.customer_id, child_name=child.child_name) if CustomerDetail.objects.filter(
            customer_id=customer.customer_id, child_name=child.child_name) else None
        if detail:
            detail.delete()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_package_add(request, _id, _cat, _pack, _type, _add):
    categories = Category.objects.all()
    packages = Package.objects.filter(category=_cat).exclude(package_id__in=OrderPackage.objects.filter(
        order_id=_id).values_list('package_id', flat=True)) if _cat != '0' else None
    box_types = BoxType.objects.all()
    main_cuisines = MainCuisine.objects.filter(package=_pack)
    sub_cuisines = SubCuisine.objects.filter(package=_pack)
    side_cuisines1 = SideCuisine1.objects.filter(package=_pack)
    side_cuisines2 = SideCuisine2.objects.filter(package=_pack)
    side_cuisines3 = SideCuisine3.objects.filter(package=_pack)
    side_cuisines4 = SideCuisine4.objects.filter(package=_pack)
    side_cuisines5 = SideCuisine5.objects.filter(package=_pack)
    last_package = OrderPackage.objects.filter(order_id=_id).last(
    ) if OrderPackage.objects.filter(order_id=_id) else None
    selected_package = Package.objects.get(
        package_id=_pack) if _pack != '0' else None
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id).last()

    if request.POST:
        form = FormOrderPackage(request.POST)
        if form.is_valid():
            package = form.save(commit=False)
            package.order_id = _id
            package.category_id = _cat
            package.package_id = _pack
            package.type = _type
            package.box_type_id = request.POST.get('box_type')
            package.main_cuisine = request.POST.get('main_cuisine')
            package.sub_cuisine = request.POST.get('sub_cuisine')
            package.side_cuisine1 = request.POST.get('side_cuisine1')
            package.side_cuisine2 = request.POST.get('side_cuisine2')
            package.side_cuisine3 = request.POST.get('side_cuisine3')
            package.side_cuisine4 = request.POST.get('side_cuisine4')
            package.side_cuisine5 = request.POST.get('side_cuisine5')
            package.unit_price = selected_package.male_price if _type == 'Jantan' else selected_package.female_price
            package.save()

            total = OrderPackage.objects.filter(
                order_id=_id).aggregate(order=Sum('total_price'))
            order.total_order = total['order']
            order.save()

            if _add == 1:
                return HttpResponseRedirect(reverse('order-package-add', args=[_id, '0', '0', '0', 0]))
            else:
                return HttpResponseRedirect(reverse('order-confirm-update', args=[_id]))
    else:
        form = FormOrderPackage(initial={'order': _id})

    msg = form.errors
    context = {
        'form': form,
        'data': order,
        'crud': 'add',
        'cat': _cat,
        'pack': _pack,
        'type': _type,
        'categories': categories,
        'packages': packages,
        'box_types': box_types,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'last_package': last_package,
        'selected_package': selected_package,
        'order_id': _id,
        'child': child,
        'msg': msg,
    }
    return render(request, 'home/order_package_add.html', context)


def order_cs_package_add(request, _id, _cat, _pack, _type):
    package = Package.objects.get(package_id=_pack)
    if request.POST:
        package = OrderPackage(
            order_id=_id,
            category_id=_cat,
            package_id=_pack,
            type=_type,
            box_type_id=request.POST.get('box_type'),
            main_cuisine=request.POST.get('main_cuisine'),
            sub_cuisine=request.POST.get('sub_cuisine'),
            side_cuisine1=request.POST.get('side_cuisine1'),
            side_cuisine2=request.POST.get('side_cuisine2'),
            side_cuisine3=request.POST.get('side_cuisine3'),
            side_cuisine4=request.POST.get('side_cuisine4'),
            side_cuisine5=request.POST.get('side_cuisine5'),
            unit_price=package.male_price if _type == 'Jantan' else package.female_price
        )
        package.save()

        total = OrderPackage.objects.filter(
            order_id=_id).aggregate(order=Sum('total_price'))
        order = Order.objects.get(order_id=_id)
        order.total_order = total['order']
        order.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_package_update(request, _id, _package, _cat, _pack, _type, _add):
    categories = Category.objects.all()
    packages = Package.objects.filter(category=_cat).exclude(package_id__in=OrderPackage.objects.filter(
        order_id=_id).values_list('package_id', flat=True).exclude(package_id=_pack)) if _cat != '0' else None
    package = OrderPackage.objects.get(order_id=_id, id=_package)
    box_types = BoxType.objects.all()
    main_cuisines = MainCuisine.objects.filter(package=_pack)
    sub_cuisines = SubCuisine.objects.filter(package=_pack)
    side_cuisines1 = SideCuisine1.objects.filter(package=_pack)
    side_cuisines2 = SideCuisine2.objects.filter(package=_pack)
    side_cuisines3 = SideCuisine3.objects.filter(package=_pack)
    side_cuisines4 = SideCuisine4.objects.filter(package=_pack)
    side_cuisines5 = SideCuisine5.objects.filter(package=_pack)
    last_child = OrderChild.objects.filter(order_id=_id).last()
    selected_package = Package.objects.get(
        package_id=_pack) if _pack != '0' else None
    order = Order.objects.get(order_id=_id)
    orders = OrderPackage.objects.filter(order_id=_id)

    first = False
    prev_id = 0
    prev_cat = 0
    prev_pack = 0
    prev_type = 0

    first_package = OrderPackage.objects.filter(order_id=_id).first()
    if first_package.id == _package:
        first = True

    for index, i in enumerate(OrderPackage.objects.filter(order_id=_id)):
        if i.id == _package:
            n_package = index + 1

    for i in reversed(OrderPackage.objects.filter(order_id=_id)):
        if i.id < _package:
            prev_id = i.id
            prev_cat = i.category_id
            prev_pack = i.package_id
            prev_type = i.type
            break

    if request.POST:
        form = FormOrderPackage(request.POST, instance=package)
        if form.is_valid():
            package = form.save(commit=False)
            package.category_id = _cat
            package.package_id = _pack
            package.type = _type
            package.box_type_id = request.POST.get('box_type')
            package.main_cuisine = request.POST.get('main_cuisine')
            package.sub_cuisine = request.POST.get('sub_cuisine')
            package.side_cuisine1 = request.POST.get('side_cuisine1')
            package.side_cuisine2 = request.POST.get('side_cuisine2')
            package.side_cuisine3 = request.POST.get('side_cuisine3')
            package.side_cuisine4 = request.POST.get('side_cuisine4')
            package.side_cuisine5 = request.POST.get('side_cuisine5')
            package.unit_price = selected_package.male_price if _type == 'Jantan' else selected_package.female_price
            package.save()

            total = OrderPackage.objects.filter(
                order_id=_id).aggregate(order=Sum('total_price'))
            order.total_order = total['order']
            order.save()

            if _add == 1:
                return HttpResponseRedirect(reverse('order-package-add', args=[_id, '0', '0', '0', 0]))
            else:
                last_package = OrderPackage.objects.filter(order_id=_id).last()
                if last_package.id == _package:
                    return HttpResponseRedirect(reverse('order-confirm-update', args=[_id]))
                else:
                    for i in OrderPackage.objects.filter(order_id=_id):
                        if i.id > _package:
                            return HttpResponseRedirect(reverse('order-package-update', args=[_id, i.id, i.category_id, i.package_id, i.type, 0]))
    else:
        form = FormOrderPackage(instance=package)

    msg = form.errors

    context = {
        'form': form,
        'data': package,
        'first_package': first,
        'n_package': n_package,
        'orders': orders,
        'prev_id': prev_id,
        'prev_cat': prev_cat,
        'prev_pack': prev_pack,
        'prev_type': prev_type,
        'last_child': last_child,
        'cat': _cat,
        'pack': _pack,
        'type': _type,
        'crud': 'update',
        'categories': categories,
        'packages': packages,
        'box_types': box_types,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'selected_package': selected_package,
        'order_id': _id,
        'msg': msg,
    }
    return render(request, 'home/order_package_update.html', context)


def order_package_cs_update(request, _id, _cat, _pack, _type):
    package = OrderPackage.objects.get(order_id=_id, package=_pack)
    order = Order.objects.get(order_id=_id)
    selected_package = Package.objects.get(package_id=_pack)

    if request.POST:
        package.category_id = _cat
        package.package_id = _pack
        package.type = _type
        package.quantity = int(request.POST.get('quantity'))
        package.box_type_id = request.POST.get('box_type')
        package.main_cuisine = request.POST.get('main_cuisine')
        package.sub_cuisine = request.POST.get('sub_cuisine')
        package.side_cuisine1 = request.POST.get('side_cuisine1')
        package.side_cuisine2 = request.POST.get('side_cuisine2')
        package.side_cuisine3 = request.POST.get('side_cuisine3')
        package.side_cuisine4 = request.POST.get('side_cuisine4')
        package.side_cuisine5 = request.POST.get('side_cuisine5')
        package.unit_price = selected_package.male_price if _type == 'Jantan' else selected_package.female_price
        package.save()

        total = OrderPackage.objects.filter(
            order_id=_id).aggregate(order=Sum('total_price'))
        order.total_order = total['order']
        order.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_package_delete(request, _id, _package):
    package = OrderPackage.objects.get(order_id=_id, id=_package)
    package.delete()

    total = OrderPackage.objects.filter(
        order_id=_id).aggregate(order=Sum('total_price'))
    order = Order.objects.get(order_id=_id)
    order.total_order = total['order']
    order.save()

    first = OrderPackage.objects.filter(order_id=_id).first()

    return HttpResponseRedirect(reverse('order-package-update', args=[_id, first.id, first.category_id, first.package_id, first.type, 0]))


def order_package_cs_delete(request, _id, _pack):
    package = OrderPackage.objects.get(order_id=_id, id=_pack)
    package.delete()

    total = OrderPackage.objects.filter(
        order_id=_id).aggregate(order=Sum('total_price'))
    order = Order.objects.get(order_id=_id)
    order.total_order = total['order']
    order.save()

    return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))


def order_confirm_update(request, _id):
    order = Order.objects.get(order_id=_id)
    last_package = OrderPackage.objects.filter(order_id=_id).last()

    if request.POST:
        form = FormOrderConfirmUpdate(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.use_photo = request.POST.get('use_photo')
            order.witnessed = request.POST.get('witnessed')
            order.info_source = request.POST.get('info_source')
            order.save()

            return HttpResponseRedirect(reverse('order-confirm', args=[_id]))
    else:
        form = FormOrderConfirmUpdate(instance=order)

    context = {
        'form': form,
        'data': order,
        'last_package': last_package,
        'crud': 'update',
    }
    return render(request, 'home/order_confirm_update.html', context)


def order_confirm(request, _id):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)

    context = {
        'data': order,
        'child': child,
        'package': package,
        'crud': 'view',
    }
    return render(request, 'home/order_confirm.html', context)


def order_submit(request, _id):
    order = Order.objects.get(order_id=_id)
    order.order_status = 'DRAFT'
    order.save()

    link_form = AreaSales.objects.get(area_id=order.regional_id).form

    return render(request, 'home/order_thankyou.html', {'link_form': link_form})


def order_cancel(request, _id):
    order = Order.objects.get(order_id=_id)
    order.order_status = 'BATAL'
    order.save()

    return HttpResponseRedirect(reverse('order-index'))


def order_confirmed(request, _id):
    order = Order.objects.get(order_id=_id)
    order.order_status = 'CONFIRMED'
    order.cs = get_current_user().username
    order.save()

    children = OrderChild.objects.filter(order_id=_id)

    _customer = Customer.objects.get(customer_phone=order.customer_phone) if Customer.objects.filter(
        customer_phone=order.customer_phone) else None
    if not _customer:
        new_customer = Customer(
            customer_name=order.customer_name,
            customer_phone=order.customer_phone,
            customer_phone2=order.customer_phone2,
            customer_address=order.customer_address,
            customer_email=order.customer_email,
            customer_district=order.customer_district,
            customer_city=order.customer_city,
            customer_province=order.customer_province,
        )
        new_customer.save()

        for child in children:
            new_detail = CustomerDetail(
                customer_id=new_customer.customer_id,
                child_name=child.child_name,
                child_birth=child.child_birth,
                child_sex=child.child_sex,
                child_father=child.child_father,
                child_mother=child.child_mother,
            )
            new_detail.save()
    else:
        _customer.customer_name = order.customer_name
        _customer.customer_phone = order.customer_phone
        _customer.customer_phone2 = order.customer_phone2
        _customer.customer_address = order.customer_address
        _customer.customer_email = order.customer_email
        _customer.customer_district = order.customer_district
        _customer.customer_city = order.customer_city
        _customer.customer_province = order.customer_province
        _customer.save()

        for child in children:
            _child = CustomerDetail.objects.get(customer_id=_customer.customer_id, child_name=child.child_name) if CustomerDetail.objects.filter(
                customer_id=_customer.customer_id, child_name=child.child_name) else None
            if not _child:
                new_detail = CustomerDetail(
                    customer_id=_customer.customer_id,
                    child_name=child.child_name,
                    child_birth=child.child_birth,
                    child_sex=child.child_sex,
                    child_father=child.child_father,
                    child_mother=child.child_mother,
                )
                new_detail.save()

    return HttpResponseRedirect(reverse('order-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='FORM')
def form_index(request):
    area_sales = AreaSales.objects.all()

    context = {
        'data': area_sales,
        'segment': 'form',
        'group_segment': 'transaction',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='FORM') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/form_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_index(request):
    orders = Order.objects.filter(regional_id__in=AreaUser.objects.filter(user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id', 'regional').exclude(order_status__in=[
        'PENDING', 'BATAL']) if request.user.position_id == 'CS' else Order.objects.filter(regional_id__in=AreaUser.objects.filter(user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id', 'regional').exclude(order_status__in=['PENDING'])

    context = {
        'data': orders,
        'segment': 'order',
        'group_segment': 'transaction',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='ORDER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/order_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_view(request, _id, _cat, _pack, _type, _crud):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)
    form = FormOrderView(instance=order)
    formChild = FormOrderChild()
    category = Category.objects.all()
    packages = Package.objects.filter(category=_cat).exclude(package_id__in=OrderPackage.objects.filter(
        order_id=_id).values_list('package_id', flat=True)) if _cat != '0' else None
    packages_upd = Package.objects.filter(category=_cat).exclude(package_id__in=OrderPackage.objects.filter(
        order_id=_id).values_list('package_id', flat=True).exclude(package_id=_pack)) if _cat != '0' else None
    box = BoxType.objects.all()
    main_cuisines = MainCuisine.objects.filter(package=_pack)
    sub_cuisines = SubCuisine.objects.filter(package=_pack)
    side_cuisines1 = SideCuisine1.objects.filter(package=_pack)
    side_cuisines2 = SideCuisine2.objects.filter(package=_pack)
    side_cuisines3 = SideCuisine3.objects.filter(package=_pack)
    side_cuisines4 = SideCuisine4.objects.filter(package=_pack)
    side_cuisines5 = SideCuisine5.objects.filter(package=_pack)
    selected_package = Package.objects.get(
        package_id=_pack) if _pack != '0' else None
    upd_package = OrderPackage.objects.get(order_id=_id, id=_crud) if _crud not in [
        '0', 'add'] else None

    msg = form.errors
    context = {
        'form': form,
        'formChild': formChild,
        'data': order,
        'child': child,
        'package': package,
        'category': category,
        'packages': packages,
        'packages_upd': packages_upd,
        'main_cuisines': main_cuisines,
        'sub_cuisines': sub_cuisines,
        'side_cuisines1': side_cuisines1,
        'side_cuisines2': side_cuisines2,
        'side_cuisines3': side_cuisines3,
        'side_cuisines4': side_cuisines4,
        'side_cuisines5': side_cuisines5,
        'selected_package': selected_package,
        'upd_package': upd_package,
        'box': box,
        'cat': _cat,
        'pack': _pack,
        'type': _type,
        'crud_det': _crud,
        'msg': msg,
        'segment': 'order',
        'group_segment': 'transaction',
        'crud': 'view',
        'status': order.order_status,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='ORDER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/order_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_cs_update(request, _id, _cat, _pack, _type):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)

    if request.POST:
        form = FormOrderCSUpdate(request.POST, instance=order)
        if form.is_valid():
            order = form.save(commit=False)
            order.customer_name = request.POST.get('customer_name')
            order.customer_phone = request.POST.get('customer_phone')
            order.customer_phone2 = request.POST.get('customer_phone2')
            order.customer_email = request.POST.get('customer_email')
            order.customer_address = request.POST.get('customer_address')
            order.customer_city = request.POST.get('customer_city')
            order.customer_district = request.POST.get('customer_district')
            order.customer_province = request.POST.get('customer_province')
            order.delivery_date = request.POST.get('delivery_date')
            order.time_arrival = request.POST.get('time_arrival')
            order.use_photo = request.POST.get('use_photo')
            order.witnessed = request.POST.get('witnessed')
            order.info_source = request.POST.get('info_source')
            order.order_note = request.POST.get('order_note')
            order.discount = int(request.POST.get('discount'))
            order.save()

            if order.order_status != 'DRAFT':
                customer = Customer.objects.get(customer_phone=order.customer_phone) if Customer.objects.filter(
                    customer_phone=order.customer_phone) else None

                if customer:
                    customer.customer_name = order.customer_name
                    customer.customer_phone = order.customer_phone
                    customer.customer_phone2 = order.customer_phone2
                    customer.customer_address = order.customer_address
                    customer.customer_email = order.customer_email
                    customer.customer_district = order.customer_district
                    customer.customer_city = order.customer_city
                    customer.customer_province = order.customer_province
                    customer.save()

                    for i in OrderChild.objects.filter(order_id=_id):
                        detail = CustomerDetail.objects.get(
                            customer_id=customer.customer_id, child_name=i.child_name) if CustomerDetail.objects.filter(customer_id=customer.customer_id, child_name=i.child_name) else None
                        if not detail:
                            new_detail = CustomerDetail(
                                customer_id=customer.customer_id,
                                child_name=i.child_name,
                                child_birth=i.child_birth,
                                child_sex=i.child_sex,
                                child_father=i.child_father,
                                child_mother=i.child_mother,
                            )
                            new_detail.save()
                else:
                    new_customer = Customer(
                        customer_name=order.customer_name,
                        customer_phone=order.customer_phone,
                        customer_phone2=order.customer_phone2,
                        customer_address=order.customer_address,
                        customer_email=order.customer_email,
                        customer_district=order.customer_district,
                        customer_city=order.customer_city,
                        customer_province=order.customer_province,
                    )
                    new_customer.save()

                    new_children = OrderChild.objects.filter(order_id=_id)
                    for i in new_children:
                        new_detail = CustomerDetail(
                            customer_id=new_customer.customer_id,
                            child_name=i.child_name,
                            child_birth=i.child_birth,
                            child_sex=i.child_sex,
                            child_father=i.child_father,
                            child_mother=i.child_mother,
                        )
                        new_detail.save()

        return HttpResponseRedirect(reverse('order-view', args=[_id, '0', '0', '0', '0']))
    else:
        form = FormOrderCSUpdate(instance=order)

    msg = form.errors

    context = {
        'form': form,
        'data': order,
        'child': child,
        'package': package,
        'cat': _cat,
        'pack': _pack,
        'type': _type,
        'crud_det': '0',
        'msg': msg,
        'segment': 'order',
        'group_segment': 'transaction',
        'crud': 'update',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='ORDER') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/order_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_index(request):
    cash_in = CashIn.objects.filter(order_id__regional_id__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-cashin_id')

    context = {
        'data': cash_in,
        'segment': 'cash-in',
        'group_segment': 'accounting',
        'crud': 'index',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CASH-IN') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cashin_index.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_add(request, _id, _msg):
    orders = Order.objects.filter(order_status__in=['DP', 'CONFIRMED'], regional_id__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id')
    order = Order.objects.get(order_id=_id) if Order.objects.filter(
        order_id=_id) else None

    if request.POST:
        form = FormCashIn(request.POST, request.FILES)
        if form.is_valid():
            cash_in = form.save(commit=False)
            cash_in.order_id = _id
            cash_in.cashin_type = request.POST.get('cashin_type')
            if cash_in.cashin_amount > Order.objects.get(order_id=_id).pending_payment:
                return HttpResponseRedirect(reverse('cashin-add', args=[_id, '1']))
            cash_in.save()

            if not settings.DEBUG:
                cash_in = CashIn.objects.get(cashin_id=cash_in.cashin_id)
                my_file = cash_in.evidence
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)

            selected_order = Order.objects.get(order_id=_id)
            if cash_in.cashin_amount == selected_order.pending_payment:
                selected_order.order_status = 'LUNAS'
            else:
                selected_order.order_status = 'DP'

            selected_order.down_payment += cash_in.cashin_amount
            selected_order.save()

            return HttpResponseRedirect(reverse('cashin-index'))
    else:
        form = FormCashIn()

    msg = form.errors
    context = {
        'form': form,
        'orders': orders,
        'order': order,
        'order_id': _id,
        'msg': _msg,
        # 'error': msg,
        'segment': 'cash-in',
        'group_segment': 'accounting',
        'crud': 'add',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CASH-IN') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cashin_add.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_view(request, _id):
    cash_in = CashIn.objects.get(cashin_id=_id)
    form = FormCashInView(instance=cash_in)
    orders = Order.objects.filter(regional_id__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id')

    context = {
        'data': cash_in,
        'form': form,
        'orders': orders,
        'segment': 'cash-in',
        'group_segment': 'accounting',
        'crud': 'view',
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CASH-IN') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cashin_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_update(request, _id, _msg):
    cash_in = CashIn.objects.get(cashin_id=_id)
    orders = Order.objects.filter(regional_id__in=AreaUser.objects.filter(
        user_id=request.user.user_id).values_list('area_id', flat=True)).order_by('-order_id')
    order = Order.objects.get(order_id=cash_in.order_id)
    amount_before = cash_in.cashin_amount

    if request.POST:
        form = FormCashInUpdate(request.POST, request.FILES, instance=cash_in)
        if form.is_valid():
            update = form.save(commit=False)
            update.cashin_type = request.POST.get('cashin_type')
            if update.cashin_amount > order.pending_payment + amount_before:
                return HttpResponseRedirect(reverse('cashin-update', args=[_id, '1']))
            update.save()

            if not settings.DEBUG:
                cash_in = CashIn.objects.get(cashin_id=cash_in.cashin_id)
                my_file = cash_in.evidence
                filename = '../../www/aqiqahon/apps/media/' + my_file.name
                with open(filename, 'wb+') as temp_file:
                    for chunk in my_file.chunks():
                        temp_file.write(chunk)

            order.down_payment = CashIn.objects.filter(
                order_id=cash_in.order_id).aggregate(cashin=Sum('cashin_amount'))['cashin'] if CashIn.objects.filter(order_id=cash_in.order_id) else 0
            order.save()

            if order.pending_payment == 0:
                order.order_status = 'LUNAS'
            else:
                order.order_status = 'DP'
            order.save()

            return HttpResponseRedirect(reverse('cashin-index'))
    else:
        form = FormCashInUpdate(instance=cash_in)

    # msg = form.errors
    context = {
        'form': form,
        'data': cash_in,
        'orders': orders,
        'segment': 'cash-in',
        'group_segment': 'accounting',
        'crud': 'update',
        'msg': _msg,
        'role': Auth.objects.filter(user_id=request.user.user_id).values_list('menu_id', flat=True),
        'btn': Auth.objects.get(user_id=request.user.user_id, menu_id='CASH-IN') if not request.user.is_superuser else Auth.objects.all(),
    }

    return render(request, 'home/cashin_view.html', context)


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def remove_evidence(request, _id):
    cash_in = CashIn.objects.get(cashin_id=_id)
    cash_in.evidence = None
    cash_in.save()

    return HttpResponseRedirect(reverse('cashin-update', args=[_id, '0']))


@login_required(login_url='/login/')
@role_required(allowed_roles='CASH-IN')
def cashin_delete(request, _id):
    cash_in = CashIn.objects.get(cashin_id=_id)
    _order_id = cash_in.order_id
    cash_in.delete()

    selected_order = Order.objects.get(order_id=_order_id)
    selected_order.down_payment = CashIn.objects.filter(
        order_id=_order_id).aggregate(cashin=Sum('cashin_amount'))['cashin'] if CashIn.objects.filter(order_id=_order_id) else 0
    selected_order.save()

    if selected_order.pending_payment == 0:
        selected_order.order_status = 'LUNAS'
    else:
        if selected_order.down_payment == 0:
            selected_order.order_status = 'CONFIRMED'
        else:
            selected_order.order_status = 'DP'
    selected_order.save()

    return HttpResponseRedirect(reverse('cashin-index'))


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_invoice(request, _id):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)
    region = AreaSales.objects.get(area_id=order.regional_id)

    hari = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Ahad']
    bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    order_id = _id.replace('/', '-')
    customer_name = order.customer_name.replace(' ', '_')
    customer_name = customer_name.replace('/', '-')

    styles = getSampleStyleSheet()
    normalStyle = styles['Normal']
    normalStyle.fontSize = 8

    filename = 'INVOICE_' + customer_name + '_' + order_id + '.pdf'
    pdf_file = canvas.Canvas(filename)

    # Add logo in the top left corner
    logo_path = '../../www/aqiqahon/apps/static/img/logo.png'
    pdf_file.drawImage(logo_path, 35, 745, width=70, height=61)

    title = "INVOICE"
    title_width = pdf_file.stringWidth(
        title, "Helvetica-Bold", 12)  # Set font to bold
    page_width, _ = A4
    pdf_file.setFont("Helvetica-Bold", 12)  # Set font to bold
    # Calculate the x position for the title to be in the top right corner
    title_x = page_width - title_width - 35  # 25 is a margin from the right edge
    pdf_file.drawString(title_x, 795, title)

    # Add address below logo
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, 725, 'Regional :')

    # Add regional info beside regional title with bold font
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(74, 725, order.regional.area_name)
    pdf_file.setFont("Helvetica", 8)
    address = 'Kantor Pusat : Jl. KH. Maulana Hasanudin No.88'
    pdf_file.drawString(35, 713, address)
    city = 'Poris, Tangerang, 15122'
    pdf_file.drawString(35, 701, city)
    phone = 'Telp/Whatsapp : 0812 9658 9090'
    pdf_file.drawString(35, 689, phone)
    web = 'www.sahabataqiqah.co.id'
    pdf_file.drawString(35, 677, web)

    # Add title start from the middle of page
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "No. Referensi"
    page_width, _ = A4
    title_x = (page_width / 2) - 35
    pdf_file.drawString(title_x, 770, title)
    # Add order_id below title
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x, 758, order.order_id)
    # Add order date below order_id with higher space
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "Tanggal Invoice"
    pdf_file.drawString(title_x, 740, title)

    months = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
              'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']
    days = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Ahad']

    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x, 728, days[order.order_date.weekday()] + order.order_date.strftime(
        ', %d ') + months[order.order_date.month - 1] + order.order_date.strftime(' %Y'))
    # Add delivery date below order date with higher space
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "Tanggal Pengiriman"
    pdf_file.drawString(title_x, 710, title)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x, 698, days[order.delivery_date.weekday()] + order.delivery_date.strftime(
        ', %d ') + months[order.delivery_date.month - 1] + order.delivery_date.strftime(' %Y'))
    # Add customer info below delivery date with higher space
    pdf_file.setFont("Helvetica-Bold", 8)
    title = "Nama Pemesan Aqiqah"
    pdf_file.drawString(title_x, 680, title)
    pdf_file.drawString(title_x, 668, order.customer_name)
    # Add customer phone below customer name
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(title_x, 656, order.customer_phone + ' / ' +
                        order.customer_phone2 if order.customer_phone2 else order.customer_phone)

    # Add customer address below customer phone
    y = 641
    address = order.customer_address.split('\n')
    for i, line in enumerate(address):
        address_width = pdf_file.stringWidth(address[i], "Helvetica", 8)
        rows = int(address_width) // 270
        for j in range(0, rows):
            y -= 13

    for line in address:
        address_paragraph = Paragraph(line, normalStyle)
        address_paragraph.wrapOn(pdf_file, 270, 0)
        address_paragraph.drawOn(pdf_file, title_x, y)
        y -= 10

    # Add customer district below customer address
    y += 1
    pdf_file.drawString(
        title_x, y, order.customer_district + ', ' + order.customer_city)
    # Add customer province below customer district
    y -= 13
    pdf_file.drawString(title_x, y, order.customer_province)

    y -= 30
    # Add table for order detail
    pdf_file.rect(35, y, 160, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(40, y + 5, 'Produk')
    pdf_file.rect(195, y, 180, 15, stroke=True)
    pdf_file.drawString(200, y + 5, 'Deskripsi')
    pdf_file.rect(375, y, 30, 15, stroke=True)
    # Calculate the width of the string 'Qty'
    qty_width = pdf_file.stringWidth('Qty', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 375 + (30 - qty_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Qty')
    pdf_file.rect(405, y, 85, 15, stroke=True)
    # Calculate the width of the string 'Harga Satuan (Rp)'
    price_width = pdf_file.stringWidth(
        'Harga Satuan (Rp)', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 405 + (85 - price_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Harga Satuan (Rp)')
    pdf_file.rect(490, y, 65, 15, stroke=True)
    # Calculate the width of the string 'Jumlah (Rp)'
    total_width = pdf_file.stringWidth('Jumlah (Rp)', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 490 + (65 - total_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Jumlah (Rp)')

    y += 15
    total = 0
    for i in range(1, package.count() + 1):
        y -= 30
        pdf_file.rect(35, y - 15, 160, 30, stroke=True)
        pdf_file.setFont("Helvetica", 8)
        qty = ' - ' + str(package[i - 1].package.quantity) + \
            ' - ' if package[i - 1].package.quantity > 0 else ''
        pdf_file.drawString(
            40, y + 5, package[i - 1].category.category_name + ' - ' + package[i - 1].package.package_name + qty)
        if package[i - 1].package.quantity > 0:
            pdf_file.drawString(40, y - 5, 'Hewan ' + package[i - 1].type)
        pdf_file.rect(195, y - 15, 180, 30, stroke=True)

        cuisines = [package[i - 1].main_cuisine, package[i - 1].sub_cuisine,
                    package[i - 1].side_cuisine1]
        row = []
        str_cuisine = ''

        for cuisine in cuisines:
            if cuisine:
                row.append(cuisine)

        cuisines = [package[i - 1].side_cuisine2, package[i - 1].side_cuisine3,
                    package[i - 1].side_cuisine4, package[i - 1].side_cuisine5]

        for j in range(0, len(row)):
            str_cuisine += row[j]
            if j < len(row) - 1 and len(cuisines) > 0:
                str_cuisine += ' - '

        pdf_file.drawString(200, y + 5, str_cuisine)

        row = []
        str_cuisine = ''
        str_box = ''

        for cuisine in cuisines:
            if cuisine:
                row.append(cuisine)

        for j in range(0, len(row)):
            str_cuisine += row[j]
            if j < len(row) - 1:
                str_cuisine += ' - '

        if str_cuisine != '' and package[i - 1].package.box > 0:
            str_box = ' - '
        str_box += str(package[i - 1].package.box) + ' Box (' + package[i -
                                                                        1].box_type.box_type_name + ')' if package[i - 1].package.box > 0 else ''

        pdf_file.drawString(200, y - 5, str_cuisine + str_box)
        pdf_file.rect(375, y - 15, 30, 30, stroke=True)
        pdf_file.setFont("Helvetica", 8)
        # Calculate the width of the string 'quantity'
        quantity_width = pdf_file.stringWidth(
            str(package[i - 1].quantity), "Helvetica", 8)
        # Calculate the center position of the rectangle
        center_x = 375 + (30 - quantity_width) / 2
        pdf_file.drawString(
            center_x, y + 5, str(package[i - 1].quantity))
        pdf_file.rect(405, y - 15, 85, 30, stroke=True)
        pdf_file.drawString(
            410, y + 5, "{:,}".format(package[i - 1].unit_price))
        pdf_file.rect(490, y - 15, 65, 30, stroke=True)
        total_price = package[i - 1].unit_price * package[i - 1].quantity
        total += total_price
        total_price_str = "{:,}".format(total_price)
        total_price_width = pdf_file.stringWidth(
            total_price_str, "Helvetica", 8)
        pdf_file.drawString(490 + 65 - total_price_width -
                            5, y + 5, total_price_str)

    y -= 30
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Sub Total'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(total)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Diskon'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.discount)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'DP'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.down_payment)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Jumlah Tertagih'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.pending_payment)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y2 = y
    y -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(35, y, 'Syarat & Ketentuan')
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y - 15, 'Pengiriman')
    pdf_file.drawString(95, y - 15, ':')
    pdf_file.drawString(
        105, y - 15, hari[int(order.delivery_date.strftime('%w')) - 1] + ', ' + order.delivery_date.strftime('%-d ') + bulan[int(order.delivery_date.strftime('%-m')) - 1] + order.delivery_date.strftime(' %Y'))
    pdf_file.drawString(35, y - 27, 'Jam Berangkat')
    pdf_file.drawString(95, y - 27, ':')
    time_arrival_minus_one_hour = datetime.datetime.strptime(
        order.time_arrival, '%H:%M') - datetime.timedelta(hours=1)
    pdf_file.drawString(
        105, y - 27, time_arrival_minus_one_hour.strftime('%H:%M'))
    pdf_file.drawString(35, y - 39, 'Jam Tiba')
    pdf_file.drawString(95, y - 39, ':')
    pdf_file.drawString(105, y - 39, order.time_arrival)
    pdf_file.drawString(35, y - 51, 'Catatan')
    pdf_file.drawString(95, y - 51, ':')

    notes = order.order_note.split('\n') if order.order_note else ''
    for i, line in enumerate(notes):
        note_width = pdf_file.stringWidth(notes[i], "Helvetica", 8)
        rows = int(note_width) // 200
        for j in range(0, rows):
            y -= 13

        notes_paragraph = Paragraph(line, normalStyle)
        notes_paragraph.wrapOn(pdf_file, 200, 100)
        notes_paragraph.drawOn(pdf_file, 105, y - 55)
        y -= 10

    y2 -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    page_width = 595.27
    text = 'Anak yang di aqiqah'
    text_x = (page_width / 2) + 35
    pdf_file.drawString(text_x, y2, text)
    pdf_file.setFont("Helvetica", 8)
    y2 -= 15
    for i in range(1, child.count() + 1):
        pdf_file.drawString(text_x, y2, str(i) + '.')
        pdf_file.drawString(text_x + 10, y2, child[i - 1].child_name)
        y2 -= 12
        sex = 'Laki-laki' if child[i - 1].child_sex == '1' else 'Perempuan'
        pdf_file.drawString(
            text_x + 10, y2, '(' + child[i - 1].child_birth.strftime('%-d') + ' ' + bulan[int(child[i - 1].child_birth.strftime('%-m')) - 1] + ' ' + child[i - 1].child_birth.strftime('%Y') + ') | ' + sex)
        y2 -= 12

    y2 -= 15
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(text_x, y2, 'Anak dari')
    pdf_file.setFont("Helvetica", 8)
    y2 -= 15
    pdf_file.drawString(
        text_x, y2, child[0].child_father)
    y2 -= 12
    pdf_file.drawString(text_x, y2, child[0].child_mother)

    y -= 81
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(
        35, y, 'Sertifikat dan Kartu Ucapan pakai foto atau tidak?')
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(
        35, y - 12, 'YA' if order.use_photo == 1 else 'TIDAK')

    y -= 27
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(35, y, 'Penyembelihan disaksikan?')
    y -= 12
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y, 'YA' if order.witnessed == 1 else 'TIDAK')

    y -= 15
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(35, y, 'Sumber Informasi?')
    y -= 12
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y, order.info_source)

    y -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(35, y, '* DP minimal 30%')

    y -= 30
    pdf_file.drawString(
        35, y, 'Pembayaran dapat dilakukan melalui transfer ke rekening :')
    y -= 15
    bank = region.bank_account.split('\n')
    for line in bank:
        bank_paragraph = Paragraph(line, normalStyle)
        bank_paragraph.wrapOn(pdf_file, 200, 100)
        bank_paragraph.drawOn(pdf_file, 35, y)
        y -= 10

    y2 -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(text_x, y2, 'Tangerang, ' + order.order_date.strftime('%-d ') +
                        bulan[int(order.order_date.strftime('%-m')) - 1] + order.order_date.strftime(' %Y'))
    y2 -= 55
    gm = User.objects.get(position='GM')
    sign_path = gm.signature.path
    pdf_file.drawImage(sign_path, text_x, y2, width=100, height=50)

    y2 -= 15
    pdf_file.drawString(text_x, y2, gm.username)
    y2 -= 12
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(text_x, y2, gm.position.position_name)

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_bap(request, _id):
    order = Order.objects.get(order_id=_id)
    child = OrderChild.objects.filter(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)
    region = AreaSales.objects.get(area_id=order.regional_id)

    hari = ['Ahad', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu']
    bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    order_id = _id.replace('/', '-')
    customer_name = order.customer_name.replace(' ', '_')
    customer_name = customer_name.replace('/', '-')

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 8
    bold_style = styles['Normal']
    bold_style.fontSize = 8
    bold_style.fontName = 'Helvetica-Bold'

    filename = 'SURAT_JALAN_' + customer_name + '_' + order_id + '.pdf'
    pdf_file = canvas.Canvas(filename)

    # Add logo in the top center
    logo_path = '../../www/aqiqahon/apps/static/img/logo.png'
    pdf_file.drawImage(logo_path, 260, 745, width=70, height=61)

    y = 725
    title = "SURAT JALAN SAHABAT AQIQAH"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 12)
    page_width, _ = A4
    title_x = (page_width / 2) - (title_width / 2)
    pdf_file.setFont("Helvetica-Bold", 12)
    pdf_file.drawString(title_x, y, title)

    y -= 50
    y2 = y
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y, 'Nama Shahibul Aqiqah (1)')
    pdf_file.drawString(135, y, ':')
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(145, y, child[0].child_name)
    y -= 12
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, y, 'Nama Pemesan')
    pdf_file.drawString(135, y, ':')
    pdf_file.drawString(145, y, order.customer_name)
    y -= 12
    pdf_file.drawString(35, y, 'No. Telepon')
    pdf_file.drawString(135, y, ':')
    pdf_file.drawString(145, y, order.customer_phone +
                        ' / ' + str(order.customer_phone2) if order.customer_phone2 else order.customer_phone)
    y -= 12
    pdf_file.drawString(35, y, 'Alamat')
    pdf_file.drawString(135, y, ':')

    y += 1
    address = order.customer_address.split('\n')
    for i, line in enumerate(address):
        address_width = pdf_file.stringWidth(address[i], "Helvetica", 8)
        rows = int(address_width) // 238
        for j in range(0, rows):
            y -= 13

    for line in address:
        address_paragraph = Paragraph(line, bold_style)
        address_paragraph.wrapOn(pdf_file, 240, 100)
        address_paragraph.drawOn(pdf_file, 145, y - 4)
        y -= 10

    y -= 2
    pdf_file.drawString(35, y, 'Tanggal Pengiriman')
    pdf_file.drawString(135, y, ':')
    pdf_file.drawString(145, y, order.delivery_date.strftime(
        '%-d ') + bulan[order.delivery_date.month - 1] + order.delivery_date.strftime(' %Y'))
    y -= 12
    pdf_file.drawString(35, y, 'Jam Tiba')
    pdf_file.drawString(135, y, ':')
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(145, y, order.time_arrival)

    # Add table right beside the customer info
    y2 -= 2
    pdf_file.rect(405, y2, 150, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    text = 'No. Order'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 150
    text_x = 405 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y2 + 5, text)
    pdf_file.rect(405, y2 - 15, 150, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    text = order.order_id
    text_width = pdf_file.stringWidth(text, "Helvetica", 8)
    text_x = 405 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y2 - 10, text)

    y -= 30
    # Add table for order detail
    pdf_file.rect(35, y, 160, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(40, y + 5, 'Produk')
    pdf_file.rect(195, y, 180, 15, stroke=True)
    pdf_file.drawString(200, y + 5, 'Deskripsi')
    pdf_file.rect(375, y, 30, 15, stroke=True)
    # Calculate the width of the string 'Qty'
    qty_width = pdf_file.stringWidth('Qty', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 375 + (30 - qty_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Qty')
    pdf_file.rect(405, y, 85, 15, stroke=True)
    # Calculate the width of the string 'Harga Satuan (Rp)'
    price_width = pdf_file.stringWidth(
        'Harga Satuan (Rp)', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 405 + (85 - price_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Harga Satuan (Rp)')
    pdf_file.rect(490, y, 65, 15, stroke=True)
    # Calculate the width of the string 'Jumlah (Rp)'
    total_width = pdf_file.stringWidth('Jumlah (Rp)', "Helvetica-Bold", 8)
    # Calculate the center position of the rectangle
    center_x = 490 + (65 - total_width) / 2
    pdf_file.drawString(center_x, y + 5, 'Jumlah (Rp)')

    y += 15
    total = 0
    for i in range(1, package.count() + 1):
        y -= 30
        pdf_file.rect(35, y - 15, 160, 30, stroke=True)
        pdf_file.setFont("Helvetica", 8)
        qty = ' - ' + str(package[i - 1].package.quantity) + \
            ' - ' if package[i - 1].package.quantity > 0 else ''
        pdf_file.drawString(
            40, y + 5, package[i - 1].category.category_name + ' - ' + package[i - 1].package.package_name + qty)
        if package[i - 1].package.quantity > 0:
            pdf_file.drawString(40, y - 5, 'Hewan ' + package[i - 1].type)
        pdf_file.rect(195, y - 15, 180, 30, stroke=True)

        cuisines = [package[i - 1].main_cuisine, package[i - 1].sub_cuisine,
                    package[i - 1].side_cuisine1, package[i - 1].side_cuisine2]
        row = []
        str_cuisine = ''

        for cuisine in cuisines:
            if cuisine:
                row.append(cuisine)

        for j in range(0, len(row)):
            str_cuisine += row[j] + ' - '

        pdf_file.drawString(200, y + 5, str_cuisine)

        cuisines = [package[i - 1].side_cuisine3,
                    package[i - 1].side_cuisine4, package[i - 1].side_cuisine5]
        row = []
        str_cuisine = ''
        str_box = ''

        for cuisine in cuisines:
            if cuisine:
                row.append(cuisine)

        for j in range(0, len(row)):
            str_cuisine += row[j]
            if j < len(row) - 1:
                str_cuisine += ' - '

        if str_cuisine != '' and package[i - 1].package.box > 0:
            str_box = ' - '
        str_box += str(package[i - 1].package.box) + ' Box (' + package[i -
                                                                        1].box_type.box_type_name + ')' if package[i - 1].package.box > 0 else ''

        pdf_file.drawString(200, y - 5, str_cuisine + str_box)
        pdf_file.rect(375, y - 15, 30, 30, stroke=True)
        pdf_file.setFont("Helvetica", 8)
        # Calculate the width of the string 'quantity'
        quantity_width = pdf_file.stringWidth(
            str(package[i - 1].quantity), "Helvetica", 8)
        # Calculate the center position of the rectangle
        center_x = 375 + (30 - quantity_width) / 2
        pdf_file.drawString(
            center_x, y + 5, str(package[i - 1].quantity))
        pdf_file.rect(405, y - 15, 85, 30, stroke=True)
        pdf_file.drawString(
            410, y + 5, "{:,}".format(package[i - 1].unit_price))
        pdf_file.rect(490, y - 15, 65, 30, stroke=True)
        total_price = package[i - 1].unit_price * package[i - 1].quantity
        total += total_price
        total_price_str = "{:,}".format(total_price)
        total_price_width = pdf_file.stringWidth(
            total_price_str, "Helvetica", 8)
        pdf_file.drawString(490 + 65 - total_price_width -
                            5, y + 5, total_price_str)

    y -= 30
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Sub Total'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(total)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Diskon'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.discount)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'DP'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.down_payment)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 15
    # create rectangle from first column to column 3
    pdf_file.rect(35, y, 455, 15, stroke=True)
    total_str = 'Jumlah Tertagih'
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica-Bold", 8)
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(490 - total_str_width - 5, y + 5, total_str)
    pdf_file.rect(490, y, 65, 15, stroke=True)
    total_str = "{:,}".format(order.pending_payment)
    total_str_width = pdf_file.stringWidth(total_str, "Helvetica", 8)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(490 + 65 - total_str_width - 5, y + 5, total_str)

    y -= 60
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.rect(35, y, 100, 15, stroke=False)
    text = 'GA'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 100
    text_x = 35 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)
    pdf_file.rect(135, y, 100, 15, stroke=False)
    text = 'Kurir'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 100
    text_x = 135 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)
    pdf_file.rect(35, y - 50, 100, 15, stroke=False)
    text = '( __________________ )'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 100
    text_x = 35 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y - 50, text)
    pdf_file.rect(135, y - 50, 100, 15, stroke=False)
    text = '( __________________ )'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 100
    text_x = 135 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y - 50, text)

    pdf_file.rect(250, y, 210, 15, stroke=True)
    pdf_file.setFont("Helvetica-Bold", 8)
    text = 'Dengan ini saya menyetujui :'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 210
    text_x = 250 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)
    pdf_file.rect(460, y, 45, 15, stroke=True)
    text = 'Checklist'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 45
    text_x = 460 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)
    pdf_file.rect(505, y, 50, 15, stroke=True)
    text = 'Penerima'
    text_width = pdf_file.stringWidth(text, "Helvetica-Bold", 8)
    box_width = 50
    text_x = 505 + (box_width - text_width) / 2
    pdf_file.drawString(text_x, y + 5, text)

    y -= 15
    pdf_file.rect(250, y, 210, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(
        255, y + 5, 'Kelengkapan isi box dari paketan sudah sesuai orderan')
    pdf_file.rect(460, y, 45, 15, stroke=True)
    pdf_file.rect(505, y - 40, 50, 55, stroke=True)
    y -= 15
    pdf_file.rect(250, y - 25, 210, 40, stroke=True)
    pdf_file.drawString(
        255, y + 5, 'Ketahanan makanan 3-4 jam setelah makanan tiba di')
    pdf_file.drawString(
        255, y - 5, 'lokasi (bersedia mengirimkan sampel basi setelah 3 jam')
    pdf_file.drawString(
        255, y - 15, 'via gosend *biaya ditanggung Sahabat Aqiqah)')
    pdf_file.rect(460, y - 25, 45, 40, stroke=True)

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')


@login_required(login_url='/login/')
@role_required(allowed_roles='ORDER')
def order_checklist(request, _id):
    order = Order.objects.get(order_id=_id)
    package = OrderPackage.objects.filter(order_id=_id)

    bulan = ['Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
             'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember']

    order_id = _id.replace('/', '-')
    customer_name = order.customer_name.replace(' ', '_')
    customer_name = customer_name.replace('/', '-')

    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    normal_style.fontSize = 8

    filename = 'CHECKLIST_' + customer_name + '_' + order_id + '.pdf'
    pdf_file = canvas.Canvas(filename)

    # Add logo in the top left corner
    logo_path = '../../www/aqiqahon/apps/static/img/logo.png'
    pdf_file.drawImage(logo_path, 35, 745, width=70, height=61)

    title = "CHECKLIST FORM"
    title_width = pdf_file.stringWidth(
        title, "Helvetica-Bold", 12)  # Set font to bold
    page_width, _ = A4
    pdf_file.setFont("Helvetica-Bold", 12)  # Set font to bold
    # Calculate the x position for the title to be in the top right corner
    title_x = page_width - title_width - 35  # 25 is a margin from the right edge
    pdf_file.drawString(title_x, 795, title)

    # Add address below logo
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(35, 725, 'Regional :')

    # Add regional info beside regional title with bold font
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(74, 725, order.regional.area_name)
    pdf_file.setFont("Helvetica", 8)
    address = 'Kantor Pusat : Jl. KH. Maulana Hasanudin No.88'
    pdf_file.drawString(35, 713, address)
    city = 'Poris, Tangerang, 15122'
    pdf_file.drawString(35, 701, city)
    phone = 'Telp/Whatsapp : 0812 9658 9090'
    pdf_file.drawString(35, 689, phone)
    web = 'www.sahabataqiqah.co.id'
    pdf_file.drawString(35, 677, web)

    y = 745
    # Add title start from the middle of page
    title = "No. Invoice"
    page_width, _ = A4
    title_x = (page_width / 2) + 35
    pdf_file.drawString(title_x, y, title)
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, order.order_id)
    y -= 12
    pdf_file.drawString(title_x, y, "Nama Pemesan")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, order.customer_name)
    y -= 12
    pdf_file.drawString(title_x, y, "Tanggal Delivery")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, order.delivery_date.strftime(
        '%-d ') + bulan[order.delivery_date.month - 1] + order.delivery_date.strftime(' %Y'))
    y -= 12
    pdf_file.drawString(title_x, y, "Checker")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, '______________________')
    y -= 12
    pdf_file.drawString(title_x, y, "Driver")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(title_x + 90, y, '______________________')
    y -= 12
    pdf_file.drawString(title_x, y, "Menu")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(
        title_x + 90, y, package[0].category.category_name + ' - ' + package[0].package.package_name)
    y -= 12
    pdf_file.drawString(title_x, y, "Jumlah Box")
    pdf_file.drawString(title_x + 80, y, ':')
    pdf_file.drawString(
        title_x + 90, y, str(package[0].package.box * package[0].quantity if package[0].package.box > 0 else package[0].quantity
                             ) + ' ' + package[0].box_type.box_type_name)

    y -= 30
    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.line(35, y, page_width - 35, y)
    y -= 15
    y2 = y
    pdf_file.drawString(40, y, 'DI ISI OLEH DRIVER')
    pdf_file.drawString(140, y, 'DI ISI OLEH CHECKER')
    y -= 10
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.setFont("Helvetica", 8)
    pdf_file.drawString(140, y + 5, 'Nasi Kebuli / Nasi Kuning / Nasi Putih')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    if package[0].main_cuisine:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].main_cuisine)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].sub_cuisine:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].sub_cuisine)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine1:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine1)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine2:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine2)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine3:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine3)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine4:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine4)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    if package[0].side_cuisine5:
        y -= 20
        pdf_file.rect(40, y, 80, 15, stroke=True)
        pdf_file.drawString(140, y + 5, package[0].side_cuisine5)
        y -= 5
        pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Kerupuk')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Acar')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Mr. Jussie / Air Mineral / Kosong')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Telor Pindang / Telor Balado')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Sertifikat')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Kantong Plastik / Tas Serut')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Boneka Panda / Boneka Domba / Mug')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'BAP & Kwitansi')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(140, y + 5, 'Sisa Masakan Olahan Daging ......')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)
    y -= 20
    pdf_file.rect(40, y, 80, 15, stroke=True)
    pdf_file.drawString(
        140, y + 5, 'Sisa Masakan Olahan Tulangan & Jeroan ......')
    y -= 5
    pdf_file.line(35, y, page_width - 35, y)

    pdf_file.setFont("Helvetica-Bold", 8)
    pdf_file.drawString(title_x, y2, 'CATATAN LAINNYA')
    y2 -= 30
    pdf_file.rect(title_x, y2, 80, 15, stroke=True)
    y2 -= 25
    pdf_file.rect(title_x, y2, 80, 15, stroke=True)
    y2 -= 25
    pdf_file.rect(title_x, y2, 80, 15, stroke=True)

    y -= 60
    title = "TTD CHECKER"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    pdf_file.rect(35, y, (page_width - 2*35) / 2, 15, stroke=False)
    pdf_file.drawString(35 + (((page_width / 2 - 35) -
                        title_width) / 2), y + 5, title)
    string = '( __________________ )'
    string_width = pdf_file.stringWidth(string, "Helvetica-Bold", 8)
    pdf_file.drawString(35 + (((page_width / 2 - 35) -
                        string_width) / 2), y - 80, string)
    title = "TTD DRIVER"
    title_width = pdf_file.stringWidth(title, "Helvetica-Bold", 8)
    pdf_file.rect(35 + (page_width - 2*35) / 2, y,
                  (page_width - 2*35) / 2, 15, stroke=False)
    pdf_file.drawString(35 + (page_width - 2*35) / 2 +
                        ((page_width - 2*35) / 2 - title_width) / 2, y + 5, title)
    pdf_file.drawString(35 + (page_width - 2*35) / 2 +
                        ((page_width - 2*35) / 2 - string_width) / 2, y - 80, string)

    pdf_file.save()

    return FileResponse(open(filename, 'rb'), content_type='application/pdf')
