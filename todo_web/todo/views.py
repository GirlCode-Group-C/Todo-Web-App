from datetime import date as date_cls, date, timedelta
import json

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt

from .models import TaskTemplate, Todo, Todos, TodoType


# -----------------------------
# LANDING PAGE - Thando's Page
# -----------------------------
def landing_page(request):
    """
    First page where user selects which categories (personal/school/work)
    they want to work with. Selection is saved in session.
    """
    if request.method == 'POST':
        selected = []

        if "personal" in request.POST:
            selected.append("personal")
        if "school" in request.POST:
            selected.append("school")
        if "work" in request.POST:
            selected.append("work")

        # Require at least one category
        if not selected:
            error_message = "Please select at least one category!"
            return render(request, 'todo/landing.html', {'error_message': error_message})

        # Store selected categories in the session
        request.session["selected_categories"] = selected
        return redirect("create_todo")

    return render(request, 'todo/landing.html')


# -----------------------------
# LEGACY HOME (kept for routing)
# -----------------------------
def home(request):
    """
    Legacy view kept for compatibility – simply redirects to create_todo.
    """
    return redirect("create_todo")


# -----------------------------
# CREATE TODO SUGGESTIONS - Celestial's Page
# -----------------------------
def create_todo(request):
    """
    Page where the user creates reusable task templates (TaskTemplate)
    for each category (personal / school / work).
    """

    # If user skipped landing_page, default to all categories
    selected_categories = request.session.get(
        "selected_categories",
        ["personal", "school", "work"]
    )

    if request.method == "POST":
        # When "Continue" is pressed, go to the scheduling page
        if "continue" in request.POST:
            return redirect("schedule_todo")

        category = None
        task_field_name = None

        # Decide which form was submitted (personal / school / work)
        if "save_personal" in request.POST:
            category = "personal"
            task_field_name = "personal_tasks"
        elif "save_school" in request.POST:
            category = "school"
            task_field_name = "school_tasks"
        elif "save_work" in request.POST:
            category = "work"
            task_field_name = "work_tasks"

        # Save non-empty task names as TaskTemplate rows
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

    # Load existing templates to show under each card
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
# SCHEDULE TODO PAGE - Celestial's Page
# -----------------------------
def schedule_todo(request):
    """
    Page where the user schedules actual Todos (new model) on specific dates
    using the templates or custom titles.
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
        # Preserve previous values in case validation fails
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

        # Validate date (not empty, not in the past, valid format)
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

        # Decide title: from template or from custom field
        title = None
        template_obj = None

        if can_save and template_id:
            try:
                template_obj = TaskTemplate.objects.get(id=template_id)
                title = template_obj.name
                # Use template description if user left description blank
                if not description:
                    description = template_obj.description
            except TaskTemplate.DoesNotExist:
                template_obj = None

        if can_save and not title and custom_title:
            title = custom_title

        # Save or update row in Todo
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

            # Clear form after successful save
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

    # Determine which category's templates to show
    selected_category = (
        request.POST.get("category")
        or request.GET.get("category")
        or previous_category
        or "personal"
    )

    # Suggestions for the currently selected category
    suggestions = TaskTemplate.objects.filter(
        category=selected_category
    ).order_by("name")

    # All scheduled todos shown in the table preview
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
def dashboard(request):
    """
    Dashboard view used by FullCalendar and the right-hand sidebar.
    Uses only the new Todo model.
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)

    # Today's, tomorrow's and this month's future todos
    todos_today = Todo.objects.filter(date=today).order_by("title")
    todos_tomorrow = Todo.objects.filter(date=tomorrow).order_by("title")
    todos_future = Todo.objects.filter(
        date__gt=tomorrow,
        date__month=today.month
    ).order_by("date", "title")

    # All templates used in the "Create New Todo" modal suggestions
    task_templates = TaskTemplate.objects.all().order_by("category", "name")

    return render(request, 'dashboard.html', {
        # todo_types is kept for compatibility with legacy parts of the UI
        'todo_types': TodoType.objects.all(),
        'task_templates': task_templates,
        'todos_today': todos_today,
        'todos_tomorrow': todos_tomorrow,
        'todos_future': todos_future,
    })


def get_todos_json(request):
    """
    Return events for FullCalendar, using only the new Todo model.
    """
    CATEGORY_COLORS = {
        "personal": "#2196f3",  # blue
        "school":   "#4caf50",  # green
        "work":     "#ff9800",  # orange
    }

    events = []
    for t in Todo.objects.all():
        events.append({
            "id": f"todo-{t.id}",         # prefixed ID used by calendar + modals
            "model": "todo",
            "title": t.title,
            "start": t.date.isoformat(),
            "color": CATEGORY_COLORS.get(t.category, "#000000"),
        })

    return JsonResponse(events, safe=False)


def get_todo_json(request, todo_id):
    """
    Returns JSON details for a single Todo (new model) or Todos (legacy model),
    depending on the prefixed ID: 'todos-4' or 'todo-7'.
    """
    if todo_id.startswith("todos-"):
        # Legacy model – kept for backward compatibility
        real_id = int(todo_id.split("-")[1])
        todo_obj = get_object_or_404(Todos, id=real_id)
        data = {
            'id': f"todos-{todo_obj.id}",
            'title': todo_obj.title,
            'description': todo_obj.description,
            'due_date': todo_obj.due_date.isoformat(),
            'todo_type': todo_obj.todo_type.id,
            'model': 'Todos',
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
            'model': 'Todo',
        }
    else:
        return JsonResponse({'error': 'Invalid ID'}, status=400)

    return JsonResponse(data)


def sidebar_partial(request):
    """
    Returns the HTML for the right-hand sidebar (Today / Tomorrow / Future),
    used by fetch() to refresh the sidebar after changes.
    """
    today = date.today()
    tomorrow = today + timedelta(days=1)

    todos_today = Todo.objects.filter(date=today).order_by("title")
    todos_tomorrow = Todo.objects.filter(date=tomorrow).order_by("title")
    todos_future = Todo.objects.filter(
        date__gt=tomorrow,
        date__month=today.month
    ).order_by("date", "title")

    html = render(request, 'partials/sidebar.html', {
        'todos_today': todos_today,
        'todos_tomorrow': todos_tomorrow,
        'todos_future': todos_future,
    }).content.decode('utf-8')

    return JsonResponse({'html': html})


@csrf_exempt
def add_todo_from_calendar(request):
    """
    Create a Todo row directly from the calendar popup.
    Expects JSON:
      { "title", "description", "category", "date", "template_id" (optional) }
    """
    if request.method == 'POST':
        data = json.loads(request.body or "{}")

        title = (data.get('title') or "").strip()
        description = (data.get('description') or "").strip()
        category = data.get('category') or "personal"
        date_str = data.get('date')
        template_id = data.get('template_id') or None

        # Basic validation
        if not title or not date_str:
            return JsonResponse(
                {'status': 'error', 'message': 'Title and date are required.'},
                status=400
            )

        # Parse "YYYY-MM-DD" into a date
        try:
            year, month, day = map(int, date_str.split('-'))
            date_obj = date_cls(year, month, day)
        except ValueError:
            return JsonResponse(
                {'status': 'error', 'message': 'Invalid date format.'},
                status=400
            )

        # Optional: link to a TaskTemplate if provided
        template_obj = None
        if template_id:
            try:
                template_obj = TaskTemplate.objects.get(id=template_id)
                if not description and template_obj.description:
                    description = template_obj.description
            except TaskTemplate.DoesNotExist:
                template_obj = None

        # Create Todo in the new model
        todo = Todo.objects.create(
            title=title,
            description=description,
            date=date_obj,
            category=category,
            template=template_obj,
        )

        return JsonResponse({'status': 'success', 'id': todo.id})

    return JsonResponse({'status': 'error', 'message': 'Invalid method.'}, status=405)


@csrf_exempt
def update_todo(request, id):
    """
    Legacy updater for the old Todos model.
    Kept for compatibility with earlier parts of the project.
    """
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
def update_todo_todo(request, id):
    """
    Update a Todo (new model) from the View/Edit modal on the dashboard.
    Expects JSON: { "title", "description", "date", "category" }.
    """
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
    """
    Legacy delete for old Todos model.
    """
    if request.method == 'POST':
        todo = Todos.objects.get(id=id)
        todo.delete()
        return JsonResponse({'status': 'deleted'})


@csrf_exempt
def delete_todo_todo(request, id):
    """
    Delete a Todo (new model) from the dashboard modal.
    """
    if request.method == 'POST':
        todo = get_object_or_404(Todo, id=id)
        todo.delete()
        return JsonResponse({'status': 'deleted'})
