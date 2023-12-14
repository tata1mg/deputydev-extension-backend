from enum import Enum

from torpedo.common_utils import CONFIG, json_file_to_dict

X_SHARED_CONTEXT = 'X-SHARED-CONTEXT'
ENVIRONMENT = CONFIG.config['ENVIRONMENT']

FEATURE_CONFIG = json_file_to_dict('./feature_config.json')


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class DB(Enum):
    FILTER_IN_BATCH_LIMIT = 40


class SQS(Enum):
    SUBSCRIBE = {'MAX_MESSAGES': 2, 'WAIT_TIME_IN_SECONDS': 5}
    LOG_LENGTH = 100


class ReorderWidget(Enum):
    TYPES = ['minimal', 'detailed']
    MINIMAL = 'minimal'
    DETAILED = 'detailed'
    PREVIOUS_SKUS_DAYS_LIMIT = 730
    MAX_USER_SKU_LIMIT = 100
    SUBSCRIBE = {'MAX_MESSAGES': 2, 'WAIT_TIME_IN_SECONDS': 5}
    HEADER = 'Previously ordered items'
    SUB_HEADER = 'Quickly re-order medicines and health products based on your previous purchases'
    CTA_V2 = {'text': 'See all the items and order', 'url': '/reorder'}
    CTA_V1 = {'view_all': 'View All Items', 'add_to_cart': 'REORDER', 'heading': 'Previously Ordered Items'}
    TARGET_URL = 'onemg://www.1mg.com/poi_details'
    MWEB_TARGET_URL = '/reorder'
    NAVIGATION = {
        'text': 'Previously ordered items',
        'icon': 'https://onemg.gumlet.io/image/upload/marketing/232d6440-f2ee-4e77-8497-2aab9a899020.png'
    }
    ORDERED_QUANTITY_LABEL = 'Last ordered quantity : {quantity} {pack_form}'
    DEFAULT_PAGE_SIZE = 10
    DEFAULT_PAGE_SIZE_FOR_NON_PAGINATED_CLIENT = 50
    VARIANT = 'Reorder Widget Shown, skus_count = {}'
    VISIBLE_AT = {"home_page": True, "medicine_page": True, "my_orders_page": True}
    FREQ_FACTOR = 0.8
    RECENCY_FACTOR = 0.2
    FALLBACK = {
        'header': "You haven't placed any order yet",
        'sub_header': 'When you place a medicine order, you can track it from here',
        'image': 'https://onemg.gumlet.io/image/upload/prifpovozciezkcvmseo.png'
    }
    REFILL_NUDGE = {
        "values": [
            {
                "display_text": "30 days",
                "label": 30,
                "ga_data": {
                    "category": "refill",
                    "action": "tap",
                    "label": "30 days"
                }
            },
            {
                "display_text": "60 days",
                "label": 60,
                "ga_data": {
                    "category": "refill",
                    "action": "tap",
                    "label": "30 days"
                }
            },
            {
                "display_text": "90 days",
                "label": 90,
                "ga_data": {
                    "category": "refill",
                    "action": "tap",
                    "label": "30 days"
                }
            }
        ],
        "refill_message": "Refill once in every",
        "bgcolor": "#EDF0FF",
        "know_more": {
            "header": "About Refill",
            "widgets": [
                {
                    "header": "Norflox-TZ RF Tablet",
                    "sub_header": "Refill Frequency: <b>10 tablets once in every 30 Days</b>",
                    "values": [
                        {
                            "header": "Start your Refill",
                            "sub_header": "Set frequency, complete checkout and payment to start your refill.",
                            "icon": "https://onemg.gumlet.io/image/upload/v1634889686/uzc9pjavggtupfg02sie.png",
                            "bg_color": "#EDF0FF"
                        },
                        {
                            "header": "We auto-apply the best discount",
                            "sub_header": "Best available discount coupon is auto-applied for next refill on the order confirmation date.",
                            "icon": "https://onemg.gumlet.io/image/upload/v1634889657/n1w4b6g5vt7y1vfnvelz.png",
                            "bg_color": "#EDF0FF"
                        },
                        {
                            "header": "Pay for each order separately",
                            "sub_header": "Pay online for subsequent orders when we notify you or the order is placed as cash on delivery.",
                            "icon": "https://onemg.gumlet.io/image/upload/v1634889673/khlxobgkomvyoior8pyq.png",
                            "bg_color": "#EDF0FF"
                        },
                        {
                            "header": "Edit, Cancel, Pause Anytime",
                            "sub_header": "Visit Manage Refill page under My Account section to edit and view upcoming order details.",
                            "icon": "https://onemg.gumlet.io/image/upload/v1634889707/su8rbh6wvtl6wjnan5bp.png",
                            "bg_color": "#EDF0FF"
                        }
                    ]
                }
            ],
            "display_text": "What is Refill and how it works?",
            "cta": {
                "text": "Know more",
                "details": {
                    "target_url": "onemg://www.1mg.com/refill/about_refill"
                },
                "action": "REDIRECT"
            }
        }
    }


class Sku(Enum):
    DEFAULT_MAX_ORDER_QUANTITY = 20
    KNOW_MORE_HEADER = 'Minimum order quantity'
    KNOW_MORE_DESCRIPTION = 'This offer price requires a minimum quantity of this product in your order. ' \
                            'A minimum order quantity allows us to offer a lower price against the item that would ' \
                            'otherwise be cost-prohibitive to ship.'
    CTA_TEXT = {True: 'Add to cart', False: 'Not available'}
    CTA_ACTION = {True: 'ADD_TO_CART', False: 'DISABLED'}
    TAG = {'best_seller': {'text': 'Bestseller', 'bg_color': '#FECF7F', 'bd_color': '#FECF7F'},
           'recommended': {'text': '1mg\'s choice', 'bg_color': '#FFCEAC', 'bd_color': '#FECF7F'}}
    SALE = {'tag': 'Sale', 'pre_text': 'Ends in'}
    ES_DLS_FIELDS = ['id', 'name', 'type', 'locations', 'price', 'product_form', 'discounted_price',
                     'sale_price_validity', 'cropped_image_urls',
                     'image_urls', 'attributes_obj.pack_size_label', 'attributes_obj.sku_pack_form_plural_name',
                     'is_visible',
                     'attributes_obj.pack_form', 'attributes_obj.item_size', 'best_seller_udp', 'recommended',
                     'total_ratings',
                     'average_rating', 'min_order_qty', 'order_limit_rule', 'units_in_pack', 'is_banned', 'saleable']


class RefillAdoptionABVariants(Enum):
    variant_a = 'control_1'
    variant_b = 'control_2'
    variant_c = 'test'
