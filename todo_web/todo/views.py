from django.shortcuts import render, redirect

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
        
        return redirect("/create-todo/")
    
    return render(request, 'todo/landing.html')