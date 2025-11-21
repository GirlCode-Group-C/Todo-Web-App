from datetime import date as date_cls 
from django.shortcuts import render, redirect
from .models import TaskTemplate, Todo


def home(request):
    """
    Temporary home view.
    Right now, it just sends users to the create-todo page.
    Later, your team can change this to the dashboard.
    """
    return redirect("create_todo")


def create_todo(request):
    """
    Create Todo (Task Template Version):
    - Shows Personal / School / Work cards depending on selected categories.
    - Each card has MULTIPLE text fields (list of tasks).
    - SAVE on a card creates TaskTemplate entries.
    - CONTINUE sends the user to the next page (for now: home).
    """

    # 1) Which categories should show?
    # If landing page sets session["selected_categories"], we use that.
    # Otherwise, we default to all three.
    selected_categories = request.session.get(
        "selected_categories",
        ["personal", "school", "work"]
    )

    if request.method == "POST":
        # CONTINUE button
        if "continue" in request.POST:
            # TODO: change "schedule" to my dashboard route later
            return redirect("schedule_todo")

        # Determine which category's SAVE button was clicked
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
            # Get all text values for that category's task inputs
            raw_tasks = request.POST.getlist(task_field_name)

            for task_text in raw_tasks:
                name = (task_text or "").strip()
                if not name:
                    continue

                # Create or reuse a template for this category + name
                TaskTemplate.objects.get_or_create(
                    name=name,
                    category=category,
                )

        # After saving, reload the page (PRG pattern)
        return redirect("create_todo")

    # 2) On GET: load suggestions (previous templates) per category
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


#Schedule

def schedule_todo(request):
    """
    Page 2: Simple scheduling page.
    - User chooses a date and category.
    - Can pick a suggested task (TaskTemplate) OR write a custom title.
    - Creates or updates a Todo entry (date + category + title + optional description).
    - You cannot schedule todos in the past.
    - Also supports deleting existing Todos.
    """

    message = ""

    # Values to keep the form filled after submit
    previous_date = ""
    previous_category = "personal"
    previous_template_id = ""
    previous_custom_title = ""
    previous_description = ""
    editing_todo_id = None  # if not None, we are editing this todo

    # 💥 Handle DELETE requests first
    if request.method == "POST" and "delete_todo" in request.POST:
        todo_id = request.POST.get("todo_id")
        if todo_id:
            try:
                todo_obj = Todo.objects.get(id=todo_id)
                todo_obj.delete()
                message = "Todo deleted successfully."
            except Todo.DoesNotExist:
                message = "Could not find the todo to delete."
        # After delete, go on to load suggestions/todos below
    # 💥 Handle SAVE (create or update)
    elif request.method == "POST" and "save_todo" in request.POST:
        # Read form values WHEN saving a todo
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

        # 🔎 Validate the date (not empty, not in the past)
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

        # Decide title: template or custom
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

        if can_save and date_value and category and title:
            # 🔁 UPDATE if editing, else CREATE
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
                    # fallback: create new if not found
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

            # Clear form fields after success
            previous_date = ""
            previous_template_id = ""
            previous_custom_title = ""
            previous_description = ""
            editing_todo_id = None
        else:
            if can_save and (not title):
                message = "Please fill at least date, category and a title (template or custom)."

    # 💥 Handle "Edit" link via GET (?edit_id=...)
    edit_id = request.GET.get("edit_id")
    if edit_id and not (request.method == "POST" and "save_todo" in request.POST):
        try:
            todo_obj = Todo.objects.get(id=edit_id)
            previous_date = str(todo_obj.date)
            previous_category = todo_obj.category
            editing_todo_id = todo_obj.id
            previous_custom_title = todo_obj.title
            previous_description = todo_obj.description or ""
            previous_template_id = todo_obj.template.id if todo_obj.template else ""
        except Todo.DoesNotExist:
            message = message or "Could not find the todo to edit."

    # For GET and after POST (both save + category-change):
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
