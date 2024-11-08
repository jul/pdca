import multipart
from wsgiref.simple_server import make_server
from json import dumps
from sqlalchemy import *
from html.parser import HTMLParser
from base64 import b64encode
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from dateutil import parser
from sqlalchemy_utils import database_exists, create_database
from urllib.parse import parse_qsl, urlparse

engine = create_engine("sqlite:///this.db")
if not database_exists(engine.url):
    create_database(engine.url)

tables = dict()

class HTMLtoData(HTMLParser):
    def __init__(self):
        global engine, tables
        self.cols = []
        self.table = ""
        self.tables= []
        self.enum =[]
        self.engine= engine
        self.meta = MetaData()
        super().__init__()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        simple_mapping = dict(
            email = UnicodeText, url = UnicodeText, phone = UnicodeText,
            text = UnicodeText, checkbox = Boolean, date = Date, time = Time,
            datetime = DateTime, file = Text
        )
        if tag == "select":
            self.enum=[]
            self.current_col = attrs["name"]
        if tag == "option":
            self.enum += [ attrs["value"] ]
        if tag == "input":
            if attrs.get("name") == "id":
                self.cols += [ Column('id', Integer, primary_key = True), ]
                return
            try:
                if attrs.get("name").endswith("_id"):
                    table,_=attrs.get("name").split("_")
                    self.cols += [ Column(attrs["name"], Integer, ForeignKey(table + ".id")) ]
                    return
            except Exception as e: print(e)

            if attrs.get("type") in simple_mapping.keys():
                self.cols += [ Column(attrs["name"], simple_mapping[attrs["type"]]), ]

            if attrs["type"] == "number":
                if attrs["step"] == "any":
                    self.cols+= [ Columns(attrs["name"], Float), ]
                else:
                    self.cols+= [ Column(attrs["name"], Integer), ]
        if tag== "form":
            self.table = urlparse(attrs["action"]).path[1:]

    def handle_endtag(self, tag):
        if tag == "select":
            self.cols+= [ Column(self.current_col,Enum(*[(k,k) for k in self.enum]))]
            self.current_col=None
            self.enum = []
        if tag=="form":
            self.tables += [ Table(self.table, self.meta, *self.cols), ]
            tables[self.table] = self.tables[-1]
            self.table = ""
            self.cols = []
            with engine.connect() as cnx:
                self.meta.create_all(engine)
                cnx.commit()
prologue = """
<style>
* {    font-family:"Sans Serif" }
body { text-align: center; }
div, table {border-spacing:0;text-align:left;width:30em;margin:auto;border:1px solid #666;border-radius:.5em;margin-bottom:1em; }
tbody tr:nth-child(odd) {  background-color: #eee;}
fieldset {  border: 1px solid #666;  border-radius: .5em; width: 30em; margin: auto; }
form { text-align: left; display:inline-block; }
input,select { margin-bottom:1em; padding:.5em;} ::file-selector-button { padding:.5em}
[value=create] { background:#ffffba} [value=delete] { background:#bae1ff}
[value=update] { background:#ffdfda} [value=search] { background:#baffc9}
[type=submit] { margin-right:1em; margin-bottom:0em; border:1px solid #333; padding:.5em; border-radius:.5em; }
</style>
<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.7.1/jquery.min.js"></script>

"""

html = f"""
<!doctype html>
<html>
<head>
{prologue}
<script>
$(document).ready(function() {{
    $("form").each((i,el) => {{
        $(el).wrap("<fieldset></fieldset>"  );
        $(el).before("<legend>" + el.action + "</legend>");
        $(el).append("<input name=_action type=submit value=create ><input name=_action type=submit value=search >")
        $(el).append("<input name=_action type=submit value=update ><input name=_action type=submit value=delete >")
        $(el).attr("enctype","multipart/form-data");
        $(el).attr("method","POST");
    }});
    $("input:not([type=hidden],[type=submit]),select").each((i,el) => {{
        $(el).before("<label>" + el.name+ "</label><br/>");
        $(el).after("<br>");
    }});
}});
</script>
</head>
<body >
<div><ul>
    <li>try <a href=/user_view?id=1 > here once you filled in your first user</a></li>
    <li>try <a href=/user_view> here is a list of all known users</a></li>
</ul></div>
    <form  action=/user >
        <input type=number name=id />
        <input type=file name=pic_file />
        <input type=text name=name />
        <input type=checkbox name=is_checked />
        <select name="prefered_pet" >
        <option value="">Please select an item</option>
            <option value="dog">Dog</option>
            <option value="cat">Cat</option>
            <option value="hamster">Hamster</option>
            <option value="spider">Spider</option>
        </select>
        <input type=email name=email />
    </form>
    <form action=/group >
        <input type=number name=id />
        <input type=text name=name />
    </form>
    <form action=/user_group >
        <input type=number name=group_id />
        <input type=number name=user_id />
    </form>
    <form action=/event  >
        <input type=number name=id />
        <input type=date name=from_date />
        <input type=date name=to_date />
        <input type=text name=text />
        <input type=number name=group_id />
    </form>
    </body>
</html>
"""


router = dict({"" : lambda fo: html,"user_view" : lambda fo : f"""
<!doctype html>
<html>
<head>
{prologue}
<script>
    $.ajax({{
        url: "/user",
        method: "POST",
        data : {{ {fo.get("id") and 'id:"%s",' % fo["id"] or "" } _action: "read"}}
    }}).done((msg) => {{
    for (var i=1; i<msg['result'][0].length;i++) {{
        $($("[name=toclone]")[0]).after($("[name=toclone]")[0].outerHTML);
    }}
    msg["result"][0].forEach((res,i) => {{
        $("span", $($("[name=toclone]")[i])).each( (h,el) => {{
            $(el).text(res[$(el).attr("name")]);
        }})
        $("[name=pic]", $($("[name=toclone]")[i])).attr("src",res["pic_file"]);
    }})
}});
</script>
</head>
<body>
<table name=toclone >
    <tr><td><label>id</label>:</td><td> <span name=id /></td></tr>
    <tr><td><label>name</label>:</td><td> <span name=name /></td></tr>
    <tr><td><label>email</label>:</td><td> <span name=email /></td></tr>
    <tr><td><label>prefered pet</label>:</td><td><span name=prefered_pet /></td></tr>
    <tr><td><label>is checked </label>:</td><td><span name=is_checked /></td></tr>
    <tr><td><label>picture</label>:</td><td><img width=200px name=pic ></td></tr>
</table>
</body>
</html>
"""})

def simple_app(environ, start_response):
    fo, fi=multipart.parse_form_data(environ)
    fo.update(**{ k: dict(
            name=fi[k].filename,
            content_type=fi[k].content_type,
            content=b64encode(fi[k].file.read())
        ) for k,v in fi.items()})
    table = route = environ["PATH_INFO"][1:]
    fo.update(**dict(parse_qsl(environ["QUERY_STRING"])))
    HTMLtoData().feed(html)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    Base = automap_base(metadata=metadata)
    Base.prepare()
    attrs_to_dict = lambda attrs : {  k: (
                    # handling of input having date/time in the name
                    "date" in k or "time" in k ) and type(k) == str
                        and parser.parse(v) or
                    # handling of input type = form havin "file" in the name of the inpur
                    "file" in k and f"""data:{fo[k]["content_type"]}; base64, {fo[k]["content"].decode()}""" or
                    # handling of boolean mapping which input begins with "is_"
                    k.startswith("is_") or [True, False][v == "on"] and v
                    for k,v in attrs.items() if v and not k.startswith("_")
    }
    if route in tables.keys():
        start_response('200 OK', [('Content-type', 'application/json; charset=utf-8')])
        with Session(engine) as session:
            try:
                action = fo.get("_action", "")
                Item = getattr(Base.classes, table)
                if action == "delete":
                    session.delete(session.get(Item, fo["id"]))
                    session.commit()
                    fo["result"] = "deleted"
                if action == "create":
                    new_item = Item(**attrs_to_dict(fo))
                    session.add(new_item)
                    session.flush()
                    ret=session.commit()
                    fo["result"] = new_item.id
                if action == "update":
                    item = session.scalars(select(Item).where(Item.id==fo["id"])).one()
                    for k,v in attrs_to_dict(fo).items():
                        setattr(item,k,v)
                    session.commit()
                    fo["result"] = item.id
                if action in { "read", "search" }:
                    result = []
                    for elt in session.execute(
                        select(Item).filter_by(**attrs_to_dict(fo))).all():
                        result += [{ k.name:getattr(elt[0], k.name) for k in tables[table].columns},]
                    fo["result"] = result
            except Exception as e:
                fo["error"] = e
                session.rollback()
    else:
        start_response('200 OK', [('Content-type', 'text/html; charset=utf-8')])

    return [ router.get(route,lambda fo:dumps(fo.dict, indent=4, default=str))(fo).encode() ]

print("Crudest CRUD of them all on port 5000...")
make_server('', 5000, simple_app).serve_forever()
