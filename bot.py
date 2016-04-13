import telepot, sys, time, redis, thread, json, requests
from pprint import pprint
from finist import Finist
TOKEN = sys.argv[1]
bot = telepot.Bot(TOKEN)

redis_conn = redis.Redis()
redis = redis.StrictRedis(host="localhost", port=6379, db=0)

API_BASE_URL = "http://localhost:5000/optimusprice/api/v0.0.1/"
PRODUCTS_URL = API_BASE_URL + "products/all"
LIKES_URL    = API_BASE_URL + "products/likes/"

SECRET = "123"

COMMAND_START   = "/start"
COMMAND_STATUS  = "/status"
COMMAND_CANCEL  = "/cancel"
COMMAND_DEBUG   = "/debug"

MSG_0 = "Good morning!"
MSG_1 = "Hi, to be notified about product prices we need your secret key ? "
MSG_2 = "Please send us your secret key from the app, otherwise we will send you to CyberTron (kidding ;)!"
MSG_3 = "Awesome, OptimusPrice will notify you about the best price for products you like."
MSG_4 = "Wrong key, man!"
MSG_5 = "Got it, we will stop notifying you!"

MESSAGE_START   = "Hey, you're selected the following items to be updated. Are you sure ?"

def handle_message(msg):
    pprint(msg)
    content_type, chat_type, chat_id = telepot.glance(msg)
    text = msg['text']    
    print content_type, chat_type, chat_id
    print "State is ", get_state(chat_id)

    if text == COMMAND_DEBUG:
        f = open('images/1.jpg', 'rb')  # some file on local disk
        bot.sendPhoto(chat_id, f)
        # show_keyboard = {'keyboard': [['Yes','No'], ['Maybe','Maybe not']]}
        # bot.sendMessage(chat_id, MSG_0, reply_markup=show_keyboard)
        hide_keyboard = {'hide_keyboard': True}
        bot.sendMessage(chat_id, 'Yo', reply_markup=hide_keyboard)
    elif text == COMMAND_CANCEL:        
        reset_subscriptions(chat_id)
        bot.sendMessage(chat_id, MSG_5)
    elif text == COMMAND_STATUS:                
        show_status(chat_id)
    elif text.startswith(COMMAND_START):        
        params = text.split()
        if len(params) == 1:
            # reset user subscriptions 
            reset_subscriptions(chat_id)
            bot.sendMessage(chat_id, MSG_1)
        else: 
            user_id = params[1] 
            # if is_valid_key(chat_id, user_id):
            authorize(chat_id, user_id)
    else : 
        # do action based on state
        if get_state(chat_id) == "approved":
            bot.sendMessage(chat_id, MSG_3)             
            show_status(chat_id)
        else:
            user_id = text
            # if is_valid_key(chat_id, user_id):
            # print "key is valid"
            authorize(chat_id, user_id)
            # else:
            # bot.sendMessage(chat_id, MSG_4)    

def show_status(chat_id):
    print "Show status ..."
    product_subscriptions = redis.smembers("optimusprice.subscriptions." + str(chat_id))    
    if len(product_subscriptions) == 0: 
        bot.sendMessage(chat_id, "You have no subscriptions!")
    else:   
        bot.sendMessage(chat_id, "You're are subscribed for the following products : ")                           
        for pp in product_subscriptions:               
            f = open('images/%s.jpg' % pp, 'rb')  # some file on local disk                
            bot.sendPhoto(chat_id, f)            

def reset_subscriptions (chat_id):    
    users = redis.srem("optimusprice.subscriptions.users", str(chat_id))                
    redis.delete("optimusprice.subscriptions." + str(chat_id))
    fsm_reset(chat_id)

def authorize(chat_id, user_id):
    fsm_approve(chat_id)
    bot.sendMessage(chat_id, MSG_3)         
    # add user to subscribed users
    redis.sadd("optimusprice.subscriptions.users", str(chat_id))                
    redis.set("optimusprice.mapping." + str(chat_id), str(user_id))                

def is_valid_key(chat_id, text):
    print "Matching key %s with %s" % (text, SECRET)
    return text == SECRET

def get_state(chat_id):
    fsm = get_fsm(chat_id)
    return fsm.state()

def get_fsm(chat_id):
    fsm = Finist(redis_conn, chat_id, "pending")
    if fsm.state() == "pending":
        # init transitions 
        fsm.on("approve", "pending", "approved")
        fsm.on("auction", "approved", "auction_in")
        fsm.on("reset", "approved", "pending")
        fsm.on("reset", "pending", "pending")
        fsm.on("reset", "auction", "pending")
    return fsm

def fsm_change_state(chat_id, state):
    fsm = get_fsm(chat_id)
    print "State before ", fsm.state()
    fsm.trigger(state)
    print "State after ", fsm.state()

def fsm_approve(chat_id):
    fsm_change_state(chat_id, "approve")

def fsm_reset(chat_id):
    fsm_change_state(chat_id, "reset")

def get_likes_for_user(user_id):  
    products = []
    print "Likes for ", user_id    
    try : 
        r = requests.get(LIKES_URL + str(user_id))
        print r
        if r.status_code == 200:        
            data = r.content.replace('\n', '')
            products = json.loads(data)['like']
            # products = [1, 2, 3, 4, 5]
        print "likes: ", products
        return r.status_code, products
    except:
        print "Connection error"
    return 500, products

def get_all_prices():  
    # f = open ("products.json", 'rw')    
    # data = f.read().replace('\n', '')    
    d = {}
    try : 
        r = requests.get(PRODUCTS_URL)
        # if r.response_code != 200:
        #     raise Exception('API IS OFFLINE')
        data = r.content.replace('\n', '')
        d = json.loads(data)
        redis.set('optimusprice.prices', data)
        return r.status_code, d
    except: 
        print "Connection error"
    return 500, d

def build_hash_from_json(data):
    # print data
    # print data["products"]
    d = {}
    for p in data['products']:
        d[p['id']] = p     
    return d    

def check_price_and_notify(delay):  
    while 1:        
        print "Notification is triggered!"   
        # loading latest products in memory 
        # build list product with decreasing prices 
        products_prices_before = build_hash_from_json(json.loads(redis.get('optimusprice.prices')))
        status_code, prices = get_all_prices()
        
        if (status_code == 200): 
            products_prices_now = build_hash_from_json(prices)
        else: 
            products_prices_now = products_prices_before

        users = redis.smembers("optimusprice.subscriptions.users")
        print "Subscribed users: ", users
        for chat_id in users:            
            user_id = redis.get("optimusprice.mapping." + str(chat_id))                                        
            # updating user subscriptions
            status_code, products = get_likes_for_user(user_id)
            if status_code == 200:
                for p in products: 
                  redis.sadd("optimusprice.subscriptions." + str(chat_id), p)


        products_ids_to_notify = []        
        print products_prices_before.keys()
        print products_prices_now.keys()
        for p in products_prices_before.keys():
            if products_prices_now.get(p) is not None:
                if float(products_prices_now.get(p)['price']) < float(products_prices_before.get(p)['price']):
                    products_ids_to_notify.append(p)    
        print "products_ids_to_notify ", products_ids_to_notify
        users = redis.smembers("optimusprice.subscriptions.users")
        print "subscribed users ", users
        for u in users:                  
            products_likes = map(int, redis.smembers("optimusprice.subscriptions." + str(u)))                    
            print "likes for user %s : %s" %(str(u), str(products_likes))
            products_intersection = set(products_ids_to_notify).intersection(products_likes)
            print "products_intersection for user %s : %s" %(str(u), str(products_intersection))
            if len(products_intersection) > 0:
                print "Notifying %s about %s" % (u,str(products_intersection))
                for pp in products_intersection:
                    bot.sendMessage(u, "Prices has changed for :" + products_prices_before.get(pp)['name'])             
                    f = open('images/%s.jpg' % pp, 'rb')  # some file on local disk
                    bot.sendPhoto(u, f)
        time.sleep(delay)

try:
    thread.start_new_thread(check_price_and_notify, (1, ))
except Exception as e:
    print e
    print "Error: unable to start thread"

print 'Booting ...'
data = get_all_prices()
bot.notifyOnMessage(handle_message)

while 1:
    pass
