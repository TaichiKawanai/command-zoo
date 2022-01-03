#compdef {{group}}

function _{{group}} () {
    local context curcontext=$curcontext state line
    declare -A opt_args
    local ret=1

    _arguments -C \
        '(-h --help)'{-h,--help}'[show help]' \
        '(-s --show)'{-s,--show}'[show only command line]' \
        '1: :__{{group}}_commands' \
        '*:: :->args' \
        && ret=0

    case $state in
        (args)
            case $words[1] in {% for val in commands %}
                ({{val["cmd"]}})
                    _arguments -C \
                        '(- :)*: :({% for arg_v in val["args"] %}{{arg_v["arg"]}} {% endfor %})' \
                        && ret=0
                    ;;{% endfor %}
            esac
            ;;
    esac

    return ret
}

__{{group}}_commands () {
    local -a _c
    _c=({% for val in commands %}
        '{{val["cmd"]}}:{{val["desc"]}}'{% endfor %}
        'help:Shows a list of commands or help for one command'
    )

    _describe -t commands Commands _c
}

_{{group}} "$@"
