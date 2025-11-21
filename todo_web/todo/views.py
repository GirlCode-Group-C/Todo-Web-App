from datetime import date as date_cls
from django.shortcuts import render, redirect
from .models import TaskTemplate, Todo


# -----------------------------
# LANDING PAGE (Noluthando's page)
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
