from django.core.paginator import Paginator


def paginate(request, objects):
    paginator = Paginator(objects, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
