from django.shortcuts import render, redirect
from .models import TaskTemplate


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
            # TODO: change "home" to your dashboard route later
            return redirect("home")

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
