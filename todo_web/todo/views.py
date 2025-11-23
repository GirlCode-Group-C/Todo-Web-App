from datetime import date as date_cls
from django.shortcuts import render, redirect, get_object_or_404
from .models import TaskTemplate, Todo, Todos, TodoType
from django.views.decorators.csrf import csrf_exempt
import json
from datetime import date, timedelta
from django.http import JsonResponse


# -----------------------------
# LANDING PAGE (teammate's page)
# -----------------------------
def landing_page(request):
    if request.method == 'POST':

        selected = []
        if "personal" in request.POST:
            selected.append("personal")
        if "school" in request.POST:
            selected.append("school")
        if "work" in request.POST:
            selected.append("work")

        if not selected:
            error_message = "Please select at least one category!"
            return render(request, 'todo/landing.html', {'error_message': error_message})

        request.session["selected_categories"] = selected

        return redirect("create_todo")

    return render(request, 'todo/landing.html')


# -----------------------------
# LEGACY HOME (not used anymore)
# -----------------------------
def home(request):
    # Not needed now, but kept for compatibility
    return redirect("create_todo")


# -----------------------------
# CREATE TODO SUGGESTIONS PAGE
# -----------------------------
def create_todo(request):
    """
    Create Todo (Task Template Version)
    """

    selected_categories = request.session.get(
        "selected_categories",
        ["personal", "school", "work"]
    )

    if request.method == "POST":
        if "continue" in request.POST:
            return redirect("schedule_todo")

        category = None
        task_field_name = None

        if "save_personal" in request.POST:
            category = "personal"
            task_field_name = "personal_tasks"
        elif "save_school" in request.POST:
            category = "school"
            task_field_name = "school_tasks"
        elif "save_work" in request.POST:
            category = "work"
            task_field_name = "work_tasks"

        if category and task_field_name:
            raw_tasks = request.POST.getlist(task_field_name)

            for task_text in raw_tasks:
                name = (task_text or "").strip()
                if not name:
                    continue

                TaskTemplate.objects.get_or_create(
                    name=name,
                    category=category,
                )

        return redirect("create_todo")

    personal_templates = TaskTemplate.objects.filter(
        category="personal"
    ).order_by("name")
    school_templates = TaskTemplate.objects.filter(
        category="school"
    ).order_by("name")
    work_templates = TaskTemplate.objects.filter(
        category="work"
    ).order_by("name")

    context = {
        "selected_categories": selected_categories,
        "personal_templates": personal_templates,
        "school_templates": school_templates,
        "work_templates": work_templates,
    }
    return render(request, "create_todo.html", context)


# -----------------------------
# SCHEDULE TODO PAGE
# -----------------------------
def schedule_todo(request):
    """
    Page 2: Scheduling page.
    """

    message = ""

    previous_date = ""
    previous_category = "personal"
    previous_template_id = ""
    previous_custom_title = ""
    previous_description = ""
    editing_todo_id = None

    # ---------- DELETE ----------
    if request.method == "POST" and "delete_todo" in request.POST:
        todo_id = request.POST.get("todo_id")
        if todo_id:
            try:
                Todo.objects.get(id=todo_id).delete()
                message = "Todo deleted successfully."
            except Todo.DoesNotExist:
                message = "Could not find the todo to delete."

    # ---------- SAVE / EDIT ----------
    elif request.method == "POST" and "save_todo" in request.POST:

        previous_date = request.POST.get("date") or ""
        previous_category = request.POST.get("category") or "personal"
        previous_template_id = request.POST.get("template_id") or ""
        previous_custom_title = (request.POST.get("custom_title") or "").strip()
        previous_description = (request.POST.get("description") or "").strip()
        editing_todo_id = request.POST.get("todo_id") or None

        date_value = previous_date
        category = previous_category
        template_id = previous_template_id
        custom_title = previous_custom_title
        description = previous_description

        can_save = True

        # Validate date
        if not date_value:
            can_save = False
            message = "Please choose a date."
        else:
            try:
                year, month, day = map(int, date_value.split("-"))
                date_obj = date_cls(year, month, day)
                if date_obj < date_cls.today():
                    can_save = False
                    message = "You cannot schedule todos in the past."
            except ValueError:
                can_save = False
                message = "Please enter a valid date."

        # Decide title
        title = None
        template_obj = None

        if can_save and template_id:
            try:
                template_obj = TaskTemplate.objects.get(id=template_id)
                title = template_obj.name
                if not description:
                    description = template_obj.description
            except TaskTemplate.DoesNotExist:
                template_obj = None

        if can_save and not title and custom_title:
            title = custom_title

        # Save or update
        if can_save and date_value and category and title:
            if editing_todo_id:
                try:
                    todo_obj = Todo.objects.get(id=editing_todo_id)
                    todo_obj.title = title
                    todo_obj.description = description
                    todo_obj.date = date_value
                    todo_obj.category = category
                    todo_obj.template = template_obj
                    todo_obj.save()
                    message = "Todo updated successfully!"
                except Todo.DoesNotExist:
                    Todo.objects.create(
                        title=title,
                        description=description,
                        date=date_value,
                        category=category,
                        template=template_obj,
                    )
                    message = "Todo saved successfully!"
            else:
                Todo.objects.create(
                    title=title,
                    description=description,
                    date=date_value,
                    category=category,
                    template=template_obj,
                )
                message = "Todo saved successfully!"

            previous_date = ""
            previous_template_id = ""
            previous_custom_title = ""
            previous_description = ""
            editing_todo_id = None
        else:
            if can_save and not title:
                message = "Please fill at least date, category and a title."

    # ---------- LOAD EDIT ----------
    edit_id = request.GET.get("edit_id")
    if edit_id:
        try:
            todo_obj = Todo.objects.get(id=edit_id)
            previous_date = str(todo_obj.date)
            previous_category = todo_obj.category
            editing_todo_id = todo_obj.id
            previous_custom_title = todo_obj.title
            previous_description = todo_obj.description or ""
            previous_template_id = todo_obj.template.id if todo_obj.template else ""
        except Todo.DoesNotExist:
            message = "Could not find the todo to edit."

    # Category selection for GET + POST
    selected_category = (
        request.POST.get("category")
        or request.GET.get("category")
        or previous_category
        or "personal"
    )

    suggestions = TaskTemplate.objects.filter(
        category=selected_category
    ).order_by("name")

    todos = Todo.objects.all().order_by("date", "category", "title")

    context = {
        "message": message,
        "selected_category": selected_category,
        "suggestions": suggestions,
        "todos": todos,
        "previous_date": previous_date,
        "previous_category": selected_category,
        "previous_template_id": previous_template_id,
        "previous_custom_title": previous_custom_title,
        "previous_description": previous_description,
        "editing_todo_id": editing_todo_id,
    }
    return render(request, "schedule_todo.html", context)

# -----------------------------
#  TODO DASHBOARD PAGE
# -----------------------------

# def dashboard(request):
#     today = date.today()
#     tomorrow = today + timedelta(days=1)
#     todos_today = Todos.objects.filter(due_date=today)
#     todos_tomorrow = Todos.objects.filter(due_date=tomorrow)
#     todos_future = Todos.objects.filter(due_date__gt=tomorrow, due_date__month=today.month)
#     todo_types = TodoType.objects.all()
#     return render(request, 'dashboard.html', {
#         'todo_types': todo_types,
#         'todos_today': todos_today,
#         'todos_tomorrow': todos_tomorrow,
#         'todos_future': todos_future
#     })

def dashboard(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Existing Todos model
    todos_today = list(Todos.objects.filter(due_date=today))
    todos_tomorrow = list(Todos.objects.filter(due_date=tomorrow))
    todos_future = list(Todos.objects.filter(due_date__gt=tomorrow, due_date__month=today.month))

    # Include Todo model too
    tasks_today = list(Todo.objects.filter(date=today))
    tasks_tomorrow = list(Todo.objects.filter(date=tomorrow))
    tasks_future = list(Todo.objects.filter(date__gt=tomorrow, date__month=today.month))

    return render(request, 'dashboard.html', {
        'todo_types': TodoType.objects.all(),
        'todos_today': todos_today + tasks_today,
        'todos_tomorrow': todos_tomorrow + tasks_tomorrow,
        'todos_future': todos_future + tasks_future,
    })


# def get_todos_json(request):
#     todos = Todos.objects.all()
#     data = [{
#         'id': t.id,
#         'title': t.title,
#         "start": t.due_date.isoformat(),
#         'color': t.todo_type.color
#     } for t in todos]
#     return JsonResponse(data, safe=False)

def get_todos_json(request):
    todos = []

    # Existing Todos
    for t in Todos.objects.all():
        todos.append({
            "id": f"todos-{t.id}",
            "model": "todos",
            "title": t.title,
            "start": t.due_date.isoformat(),
            "color": t.todo_type.color,
        })

    # Add Todo model
    CATEGORY_COLORS = {
        "personal": "#2196f3",
        "school": "#4caf50",
        "work": "#ff9800",
    }

    for t in Todo.objects.all():
        color = CATEGORY_COLORS.get(t.category, "#000000")
        todos.append({
            "id": f"todo-{t.id}",
            "model": "todo",
            "title": t.title,
            "start": t.date.isoformat(),
            "color": color,
        })

    return JsonResponse(todos, safe=False)


# def get_todo_json(request, todo_id):
#     todo = get_object_or_404(Todos, id=todo_id)
#     data = {
#         'id': todo.id,
#         'title': todo.title,
#         'description': todo.description,
#         'due_date': todo.due_date.isoformat(),
#         'todo_type': todo.todo_type.id,
#     }
#     return JsonResponse(data)

# def get_todo_json(request, todo_id):
#     model, id = todo_id.split("-")

#     if model == "todos":
#         obj = get_object_or_404(Todos, id=id)
#         return JsonResponse({
#             "model": "todos",
#             "id": obj.id,
#             "title": obj.title,
#             "description": obj.description,
#             "due_date": obj.due_date.isoformat(),
#             "todo_type": obj.todo_type.id,
#         })

#     else:  # Todo
#         obj = get_object_or_404(Todo, id=id)
#         return JsonResponse({
#             "model": "todo",
#             "id": obj.id,
#             "title": obj.title,
#             "description": obj.description,
#             "due_date": obj.date.isoformat(),
#             "category": obj.category,
#         })

def get_todo_json(request, todo_id):
    """
    Supports prefixed IDs from calendar/sidebar: todos-4 or todo-7
    """
    if todo_id.startswith("todos-"):
        real_id = int(todo_id.split("-")[1])
        todo_obj = get_object_or_404(Todos, id=real_id)
        data = {
            'id': f"todos-{todo_obj.id}",
            'title': todo_obj.title,
            'description': todo_obj.description,
            'due_date': todo_obj.due_date.isoformat(),
            'todo_type': todo_obj.todo_type.id,
            'model': 'Todos'
        }
    elif todo_id.startswith("todo-"):
        real_id = int(todo_id.split("-")[1])
        todo_obj = get_object_or_404(Todo, id=real_id)
        CATEGORY_COLORS = {
            "personal": "#4caf50",
            "school": "#2196f3",
            "work": "#ff9800",
        }
        data = {
            'id': todo_obj.id,
            'title': todo_obj.title,
            'description': todo_obj.description,
            'due_date': todo_obj.date.isoformat(),
            'todo_type': todo_obj.category,
            'color': CATEGORY_COLORS.get(todo_obj.category, '#000000'),
            'model': 'Todo'
        }
    else:
        return JsonResponse({'error': 'Invalid ID'}, status=400)

    return JsonResponse(data)




# def sidebar_partial(request):
#     today = date.today()
#     tomorrow = today + timedelta(days=1)
#     todos_today = Todos.objects.filter(due_date=today)
#     todos_tomorrow = Todos.objects.filter(due_date=tomorrow)
#     todos_future = Todos.objects.filter(due_date__gt=tomorrow, due_date__month=today.month)

#     html = render(request, 'partials/sidebar.html', {
#         'todos_today': todos_today,
#         'todos_tomorrow': todos_tomorrow,
#         'todos_future': todos_future
#     }).content.decode('utf-8')

#     return JsonResponse({'html': html})

def sidebar_partial(request):
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Existing Todos model
    todos_today = list(Todos.objects.filter(due_date=today))
    todos_tomorrow = list(Todos.objects.filter(due_date=tomorrow))
    todos_future = list(Todos.objects.filter(
        due_date__gt=tomorrow,
        due_date__month=today.month
    ))

    # Include Todo model
    tasks_today = list(Todo.objects.filter(date=today))
    tasks_tomorrow = list(Todo.objects.filter(date=tomorrow))
    tasks_future = list(Todo.objects.filter(
        date__gt=tomorrow,
        date__month=today.month
    ))

    # Merge both model sets
    combined_today = todos_today + tasks_today
    combined_tomorrow = todos_tomorrow + tasks_tomorrow
    combined_future = todos_future + tasks_future

    html = render(request, 'partials/sidebar.html', {
        'todos_today': combined_today,
        'todos_tomorrow': combined_tomorrow,
        'todos_future': combined_future
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
    
# @csrf_exempt
# def update_todo_todo(request, id):
#     if request.method == 'POST':
#         data = json.loads(request.body)
#         todo = get_object_or_404(Todo, id=id)
#         todo.title = data.get("title", todo.title)
#         todo.description = data.get("description", todo.description)
#         todo.date = data.get("date", todo.date)
#         todo.category = data.get("category", todo.category)
#         todo.save()
#         return JsonResponse({'status': 'updated'})
    
@csrf_exempt
def update_todo_todo(request, id):
    if request.method == 'POST':
        data = json.loads(request.body)
        todo = get_object_or_404(Todo, id=id)
        todo.title = data['title']
        todo.description = data.get('description', '')
        todo.date = data['date']
        todo.category = data['category']
        todo.save()
        return JsonResponse({'status': 'updated'})



@csrf_exempt
def delete_todo(request, id):
    if request.method == 'POST':
        todo = Todos.objects.get(id=id)
        todo.delete()
        return JsonResponse({'status': 'deleted'})

@csrf_exempt
def delete_todo_todo(request, id):
    if request.method == 'POST':
        todo = get_object_or_404(Todo, id=id)
        todo.delete()
        return JsonResponse({'status': 'deleted'})



