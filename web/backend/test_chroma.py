from django.conf import settings
import chromadb

chroma_client = chromadb.HttpClient(host='chromadb', port=8000)

# xem tất cả collections
collection = chroma_client.get_collection(name="my_reference_documents")


# 1. Lấy danh sách tất cả ID đang có
# all_ids = collection.get()['ids']

# 2. Nếu có dữ liệu thì tiến hành xóa
# if all_ids:
#     collection.delete(ids=all_ids)
#     print(f"Đã xóa sạch {len(all_ids)} chunks.")
# else:
#     print("Collection đã trống sẵn rồi.")


# đếm số vector
print("🔢 Total vectors:", collection.count())


