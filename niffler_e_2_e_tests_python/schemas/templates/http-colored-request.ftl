<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset = UTF-8">
    <script src="static/libs/jquery.min.js" crossorigin="anonymous"></script>

    <link href="static/libs/bootstrap.min.css" rel="stylesheet" crossorigin="anonymous">
    <script src="static/libs/bootstrap.min.js" crossorigin="anonymous"></script>

    <link type="text/css" href="static/libs/github.min.css" rel="stylesheet"/>
    <script type="text/javascript" src="static/libs/highlight.min.js"></script>
    <script type="text/javascript" src="static/libs/bash.min.js"></script>
    <script type="text/javascript" src="static/libs/json.min.js"></script>
    <script type="text/javascript" src="static/libs/xml.min.js"></script>
    <script type="text/javascript">hljs.initHighlightingOnLoad();</script>

    <style>
        pre {
            white-space: pre-wrap;
        }
    </style>
</head>
<body>
<div>
    <pre><code>{% if request.method %}{{request.method}}{% else %}GET{% endif %} to {% if request.url %}{{request.url}}{% else %}None{% endif %}</code></pre>
</div>

{% if request.body %}
    <h4>Body</h4>
    <div>
        <pre><code>{{request.body}}</code></pre>
    </div>
{% endif %}


{% if request.headers %}
    <h4>Headers</h4>
    <div>
    {% for key, value in request.headers.items() %}
        <div>
            <pre><code><b>{{key}}</b>: {{value}}</code></pre>
        </div>
    {% endfor %}
    </div>
{% endif %}


{% if request.cookies %}
    <h4>Cookies</h4>
    <div>
    {% for key, value in request.cookies.items() %}
        <div>
            <pre><code><b>{{key}}</b>: {{value}}</code></pre>
        </div>
    {% endfor %}
    </div>
{% endif %}

{% if curl %}
    <h4>Curl</h4>
    <div>
        <pre><code>{{curl}}</code></pre>
    </div>
{% endif %}
</body>
</html>