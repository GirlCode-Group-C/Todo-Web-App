from django import template

register = template.Library()

CATEGORY_COLORS = {
    "personal": "#2196f3",
    "school": "#4caf50",
    "work": "#ff9800",
}


@register.inclusion_tag("partials/todo_card.html")
def render_card(t):
    # determine if it's Todos or Todo
    model = t.__class__.__name__.lower()

    if model == "todos":
        return {
            "id": f"todos-{t.id}",
            "title": t.title,
            "description": t.description,
            "date": t.due_date,
            "type": t.todo_type.id,
            "color": t.todo_type.color,
            "category_name": t.todo_type.name,
        }

    else:  # Todo model
        return {
            "id": f"todo-{t.id}",
            "title": t.title,
            "description": t.description,
            "date": t.date,
            "type": t.category,
            "color": CATEGORY_COLORS.get(t.category, "#000000"),
            "category_name": t.category.title(),
        }
