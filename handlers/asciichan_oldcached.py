from handlers.handlerBase import AppHandler
from google.appengine.ext import db
import urllib2
import logging
import time
from xml.dom import minidom

# Funciones

IP_URL = "http://api.hostip.info/?ip="
def get_coords(ip):
    #ip de pega para que funcione en local
    #para borrar en produccion
    ip = "4.2.2.2"
    ip = "23.24.209.141"
    url = IP_URL + ip
    content = None
    try:
        content = urllib2.urlopen(url).read()
    except URLError:
        return

    if content:
        #parse the xml and find the coordinates
        d = minidom.parseString(content)
        coords = d.getElementsByTagName("gml:coordinates")
        if coords and coords[0].childNodes[0].nodeValue:
            lon, lat = coords[0].childNodes[0].nodeValue.split(',')
            #GeoPt is a data type of google app engine
            # to store latitud and longitud
            return db.GeoPt(lat, lon)

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&scale=2&sensor=false&"
def gmaps_img(points):
    markers = '&'.join('markers=%s,%s' % (p.lat, p.lon)
                        for p in points)
    return GMAPS_URL + markers

# Creamos una entidad de la base de datos para guardar arte ascii

class Art(db.Model):
    title = db.StringProperty(required = True)
    art = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()

CACHE = {}
def top_arts(update = False):
    key = 'top'
    if not update and key in CACHE:
        arts = CACHE[key]
    else:
        #imprime un mensaje en la consola cadda vez que accedamos a la BBDD
        logging.error("DB QUERY")
        arts = db.GqlQuery("SELECT * "
                           "FROM Art "
                           "ORDER BY created DESC")
        #prevent the running of multiple queries
        arts = list(arts)
        CACHE[key] = arts
    return arts

class AsciiPage(AppHandler):
    def render_front(self, title="", art="", error=""):
        arts = top_arts()

        #find which arts have coords
        '''points = []
        for a in arts:
            if a.coords:
                points.append(a.coords)'''
        points = filter(None, (a.coords for a in arts))
        
        #if we have any arts coords, make an image url
        img_url = None
        if points:
            img_url = gmaps_img(points)
        
        #display the image url
        self.render("/front.html", title=title, art=art,
                    error=error, arts=arts, img_url=img_url)
    
    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if title and art:
            a = Art(title=title, art=art)
            #lookup the user's coordinates from their IP
            coords = get_coords(self.request.remote_addr)
            #if we have coordinates, add them to the Art
            if coords:
                a.coords = coords
            
            a.put()
            #rerun the query and update the cache
            time.sleep(.04)
            top_arts(True)
            
            self.redirect("/")
        else:
            error = "we need both a title and some artwork!"
            self.render_front(title, art, error)

