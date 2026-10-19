from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Pagination par défaut ; le client peut ajuster la taille via `page_size`."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200
