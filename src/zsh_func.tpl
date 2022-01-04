#compdef {{group}}

function _{{group}} () {
    local context curcontext=$curcontext state line
    declare -A opt_args
    local ret=1

    _arguments -C \
        '(-h --help)'{-h,--help}'[show help]' \
        '(-s --show)'{-s,--show}'[show only command line]' \
        '1: :__{{group}}_commands' \
        '2: :->args' \
        '*: :->files' \
        && ret=0

    case $state in
        (args)
            case $words[2] in{% for val in commands %}
                {{val["cmd"]}})
                        {% if val["args"]  %}_arguments -C '*: :({% for arg_v in val["args"] %}{{arg_v["arg"]}} {% endfor %})' && {% endif %}\
                        {% if val["line"]  %}_files -W `pwd`/ && {% endif %}\
                        ret=0
                    ;;{% endfor %}
            esac
            ;;
        (files)
           here=`pwd`
           _files -W $here/
    esac

    return ret
}

__{{group}}_commands () {
    local -a _c
    _c=({% for val in commands %}
        '{{val["cmd"]}}:{% if val["desc"]  %}{{val["desc"]}}{% else %}perform {{val["cmd"]}}{% endif %}'{% endfor %}
    )

    _describe -t commands Commands _c
}

_{{group}} "$@"
