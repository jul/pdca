<!DOCTYPE html>
<html>
<head>
<%include file="prologue.mako" />
<%block name="include_head" />
</head>
<body >
<div class=bandeau  >
    <a class=CRUD href=/>CRUD</a> /
    <a class=login href=/login>login</a> /
    <a class=users href=/user_view>users</a> /
    <a class=thread href=/comment>thread</a> /
    <a class=graph href=/svg>graph</a>
    <img height=48px width=48px  style=border-radius:24px src="${fo.get("_user_pic",[""])[0] }">
</div>
<div class=spacer >
</div>
${self.body() }
</body>
</html>

