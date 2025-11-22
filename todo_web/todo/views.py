from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from .models import Todos, TodoType
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import date, timedelta

def landing_page(request):
    return render(request, 'todo/landing.html')


def dashboard(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    todos_today = Todos.objects.filter(due_date=today)
    todos_tomorrow = Todos.objects.filter(due_date=tomorrow)
    todos_future = Todos.objects.filter(due_date__gt=tomorrow, due_date__month=today.month)
    todo_types = TodoType.objects.all()
    return render(request, 'dashboard.html', {
        'todo_types': todo_types,
        'todos_today': todos_today,
        'todos_tomorrow': todos_tomorrow,
        'todos_future': todos_future
    })

def get_todos_json(request):
    todos = Todos.objects.all()
    data = [{
        'id': t.id,
        'title': t.title,
        "start": t.due_date.isoformat(),
        'color': t.todo_type.color
    } for t in todos]
    return JsonResponse(data, safe=False)

def get_todo_json(request, todo_id):
    todo = get_object_or_404(Todos, id=todo_id)
    data = {
        'id': todo.id,
        'title': todo.title,
        'description': todo.description,
        'due_date': todo.due_date.isoformat(),
        'todo_type': todo.todo_type.id,
    }
    return JsonResponse(data)

def sidebar_partial(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)
    todos_today = Todos.objects.filter(due_date=today)
    todos_tomorrow = Todos.objects.filter(due_date=tomorrow)
    todos_future = Todos.objects.filter(due_date__gt=tomorrow, due_date__month=today.month)

    html = render(request, 'partials/sidebar.html', {
        'todos_today': todos_today,
        'todos_tomorrow': todos_tomorrow,
        'todos_future': todos_future
    }).content.decode('utf-8')

    return JsonResponse({'html': html})


@csrf_exempt
def add_todo_from_calendar(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        todo_type = TodoType.objects.get(id=data['todo_type'])
        Todos.objects.create(
            todo_type=todo_type,
            title=data['title'],
            description=data.get('description', ''),
            due_date=data['due_date']
        )
        return JsonResponse({'status': 'success'})


@csrf_exempt
def update_todo(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        todo = Todos.objects.get(id=id)
        todo.title = data['title']
        todo.description = data['description']
        todo.due_date = data['due_date']
        todo.todo_type_id = data['todo_type']
        todo.save()
        return JsonResponse({'status': 'updated'})

@csrf_exempt
def delete_todo(request, id):
    if request.method == 'POST':
        todo = Todos.objects.get(id=id)
        todo.delete()
        return JsonResponse({'status': 'deleted'})

