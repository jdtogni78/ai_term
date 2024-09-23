def app_alias(self, alias_name):
    return '''
        function {name} () {{
            TF_PYTHONIOENCODING=$PYTHONIOENCODING;
            export TF_SHELL=bash;
            export TF_ALIAS={name};
            export TF_SHELL_ALIASES=$(alias);
            export TF_HISTORY=$(fc -ln -10);
            export PYTHONIOENCODING=utf-8;
            TF_CMD=$(
                thefuck {argument_placeholder} "$@"
            ) && eval "$TF_CMD";
            unset TF_HISTORY;
            export PYTHONIOENCODING=$TF_PYTHONIOENCODING;
            {alter_history}
        }}
    '''.format(
        name=alias_name,
        argument_placeholder=ARGUMENT_PLACEHOLDER,
        alter_history=('history -s $TF_CMD;'
                       if settings.alter_history else ''))

def get_corrected_commands(command):
    corrected_commands = (
        corrected for rule in get_rules()
        if rule.is_match(command)
        for corrected in rule.get_corrected_commands(command))
    return organize_commands(corrected_commands)

def select_command(corrected_commands):
    try:
        selector = CommandSelector(corrected_commands)
    except NoRuleMatched:
        logs.failed('No fucks given' if get_alias() == 'fuck'
                    else 'Nothing found')
        return

    if not settings.require_confirmation:
        logs.show_corrected_command(selector.value)
        return selector.value

    logs.confirm_text(selector.value)

    for action in read_actions():
        if action == const.ACTION_SELECT:
            sys.stderr.write('\n')
            return selector.value
        elif action == const.ACTION_ABORT:
            logs.failed('\nAborted')
            return
        elif action == const.ACTION_PREVIOUS:
            selector.previous()
            logs.confirm_text(selector.value)
        elif action == const.ACTION_NEXT:
            selector.next()
            logs.confirm_text(selector.value)