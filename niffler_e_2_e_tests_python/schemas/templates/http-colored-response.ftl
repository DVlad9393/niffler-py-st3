<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8">
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
    <h4>Status code</h4>
    <pre><code><b>{{ response.status_code if response and response.status_code is not none else "Unknown" }}</b></code></pre>
</div>

{% if response and response.url %}
    <div>
        <pre><code>{{ response.url }}</code></pre>
    </div>
{% endif %}

{% if response and response.headers %}
    <h4>Headers</h4>
    <div>
        {% for key, value in response.headers.items() %}
            <div>
                <pre><code><b>{{ key }}</b>: {{ value }}</code></pre>
            </div>
        {% endfor %}
    </div>
{% endif %}

{% if response and response.text %}
    <h4>Body</h4>
    <div>
        <pre><code>{{ response.text }}</code></pre>
    </div>
{% endif %}

{% if response and response.cookies %}
    <h4>Cookies</h4>
    <div>
        {% for key, value in response.cookies.items() %}
            <div>
                <pre><code><b>{{ key }}</b>: {{ value }}</code></pre>
            </div>
        {% endfor %}
    </div>
{% endif %}

</body>
</html>