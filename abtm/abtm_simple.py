from ruamel import yaml
import html


class DotCoder:
    def __init__(self):
        self.states = {}
        self.tree = {}
        self.colors = {}
        self.node_dotcodes = {}
        self.color_types = {
            'action'   : 'green',
            'condition': 'orange',
            'sequence' : 'white',
            'skipper'  : 'white',
            'selector' : 'white',
            'fallback' : 'white',
            'parallel' : 'white',
            'template' : '#9262d1',
            'expanded' : '#fde910'
        }

        self.hat_types = {
            'action'   : '',
            'condition': '',
            'sequence' : '-&gt;',
            'skipper'  : '=&gt;',
            'selector' : '?',
            'fallback' : '?',
            'parallel' : '=',
            'template' : '&lt;...&gt;',
            'expanded' : '&gt;...&lt;'
        }

        self.expanded = {}
        self.state_names = ['RUNNING', 'SUCCESS', 'FAILURE', 'UNDEFINED']

        self.root = ""
        self.cluster_iterator = 0
        self.use_clusters = True
        self.view_params = {
            'compact': False,
            'states' : False,
            'details': False
        }
        self.state_colors = ['red', 'green', 'black', 'grey']

        self.label = ["""
                        <
                            <table border='1' cellborder='0' bgcolor="##bgcolor">
                            <tr><td>##hat</td></tr>
                            <tr><td>##name</td></tr>
                      """,
                      """
                              <tr><td>##expr</td></tr>
                      """,
                      """
                          <tr><td>##wstateword</td></tr>
                      """,
                      """
                              <tr><td bgcolor="##state"><font point-size='3'> </font></td></tr>
                              </table>
                          >
                      """]

    def get_label_template(self, expr=False, state_word=False):
        return self.label[0] + (self.label[1] if expr else "") + (self.label[2] if state_word else "") + self.label[-1]

    def set_states(self, changed_states):
        ch = yaml.safe_load(changed_states)
        # ch = yaml.safe_load(ch['data'])
        for _n in ch:
            n = _n[9:]
            self.states[n] = ch[_n]

    def get_root(self):
        for z in self.tree:
            if 'parent' in self.tree[z] and (self.tree[z]['parent'] == '' or self.tree[z]['parent'] is None):
                return z
            if 'root' in self.tree[z]:
                return z
        return ''

    def tree_from_yaml(self, yaml_str):
        y = yaml.safe_load(yaml_str)
        # n = None
        if 'nodes' in y:
            n = y.get('nodes')
        else:
            n = y
        for z in n:
            self.tree[z] = n[z]
            self.states[z] = 3
        self.root = self.get_root()

    def expand_templated_node(self, node):
        if node in self.tree:
            self.expanded[node] = self.tree[node]['view_children']
            if 'children' in self.tree[node]:
                self.tree[node]['view_children'] = self.tree[node]['children']
            else:
                self.tree[node]['view_children'] = []

    def hide_templated_node(self, node):
        if node in self.tree:
            self.tree[node]['view_children'] = self.expanded[node]
            self.expanded.pop(node)

    def get_children_keyword(self, name):
        children = ""
        print(name)
        print(self.tree[name])
        if 'view_children' in self.tree[name] and not (self.tree[name]['view_children'] is None) and len(
                self.tree[name]['view_children']) > 0:
            children = 'view_children'
        if 'view_children' not in self.tree[name] and 'children' in self.tree[name] and not (
                self.tree[name]['children'] is None) and len(self.tree[name]['children']) > 0:
            children = 'children'
        return children

    def get_next_cluster_name(self):
        self.cluster_iterator += 1
        if not self.view_params['compact']:
            return "subgraph cluster_" + str(self.cluster_iterator)
        else:
            return "subgraph hren_kakoi_to" + str(self.cluster_iterator)

    def rec_make_clusters(self, name, tabscount=0):
        code = ""
        children = self.get_children_keyword(name)

        if len(children) > 0:
            code += '\t' * tabscount + self.get_next_cluster_name() + " {\n"
            code += '\t' * (tabscount + 1) + 'color=transparent;\n'

        extra_tab = 0
        if len(children) > 0:
            extra_tab = 1
        code += '\t' * (tabscount + extra_tab) + self.node_dotcodes[name]

        if len(children) > 0:
            for child in self.tree[name][children]:
                code += self.rec_make_clusters(child, tabscount + 1)

        if len(children) > 0:
            code += '\t' * tabscount + "}\n"

        return code

    def rec_make_edges(self, name, tabscount=0):
        code = ""
        children = self.get_children_keyword(name)

        if len(children) > 0:
            for child in self.tree[name][children]:
                code += '\t' * tabscount + '\"' + name + '\" -> \"' + child + "\";\n"
            for child in self.tree[name][children]:
                code += self.rec_make_edges(child, tabscount + 1)

        return code

    def rec_make_ranks(self, names, tabscount=0):
        code = "\t" * tabscount + "{ rank=same; "
        new_names = []

        for i, name in enumerate(names):
            code += " " + name
            if i != len(names) - 1:
                code += ","
            else:
                code += "}"
            children = self.get_children_keyword(name)

            if len(children) > 0:
                new_names += self.tree[name][children]

        if len(new_names) > 0:
            code += self.rec_make_ranks(new_names, tabscount)

        return code

    def get_label(self, name, hat, bgcolor, expr='', state_word=False):
        lbl = self.get_label_template(len(expr) > 0, state_word)
        state = self.states[name]
        state_word = self.state_names[state]
        return lbl.replace('##name', name) \
            .replace('##hat', hat) \
            .replace('##bgcolor', bgcolor) \
            .replace('##state', self.state_colors[state]) \
            .replace('##expr', expr) \
            .replace('##wstateword', state_word)

    def get_dotcode(self, runtime=False):
        code = ""
        code += "digraph g {\n"
        code += "node [shape=rectangle, style=filled, color=white];\n"
        self.root = self.get_root()
        self.node_dotcodes = {}
        for name in self.tree:
            node = self.tree[name]
            desc = ""
            _type = node['type']
            if 'template_type' in node and name not in self.expanded:
                _type = node['template_type']
            # color = ""
            hat = ""
            if _type == 'action' or _type == 'condition':
                for key in ['expr', 'expression', 'script']:
                    if key in node:
                        desc = str(node[key])
                desc = desc.replace(';', ';!@')
                desc = html.escape(desc)
                desc = desc.replace(';!@', ';<br/>')
            elif _type[:2] == 't/' or _type[:9] == 'template/':
                desc = _type
                if 'view' in node:
                    desc += '<br/>' + html.escape(yaml.dump(node['view']))

            if _type == 'action' or _type == 'condition':
                color = self.color_types[_type]
            elif _type[:2] == 't/' or _type[:9] == 'template/':
                if name in self.expanded:
                    color = self.color_types['expanded']
                    hat = self.hat_types['expanded']
                else:
                    color = self.color_types['template']
                    hat = self.hat_types['template']
            else:
                color = self.color_types[_type]
                if name in self.expanded:
                    color = self.color_types['expanded']

            if _type in self.hat_types:
                hat = self.hat_types[_type]

            # fontcolor = 'black'
            # if runtime and type == 'condition':
            #     fontcolor = 'red'

            node_name = '\"' + name + '\"'

            if not self.view_params['details']:
                desc = ""

            state_word = self.view_params['states'] and _type != 'action'

            node_str = node_name + "[label=" + self.get_label(name, hat, color, desc, state_word) + "];\n"
            # "shape=" + ('cds' if type == 'action' else 'rectangle') +\

            self.node_dotcodes[name] = node_str

        self.cluster_iterator = 0
        code += self.rec_make_clusters(self.root, 1)
        code += self.rec_make_edges(self.root, 1)

        # code += "rankdir=TD;\n"
        # code += self.rec_make_ranks([self.root], 1)
        code += '\n}'
        return code


if __name__ == '__main__':
    yaml_code = """
    root: root
    nodes:
      root:
        parent: ""
        type: sequence
        children: [A, V]

      A:
        parent: root
        type: condition
        expr: "a > b"
        true_state: S
        false_state: R

      V:
        parent: root
        type: t/latch
        child: B
        view_children: B

      B:
        parent: V
        type: action
        expr: "c:= 1"
    """

    yaml_code2 = """
    V:
      template_type: t/latch
      type: skipper
      name: V
      child: B
      parent: root
      __LOAD__: __LOAD__
      children:
        - _V_mask
        - B
      view_children:
        - B
    B:
      parent: V
      expr: !<!> c:= 23
      type: action
    _V_mask:
      type: skipper
      __LOAD__: __LOAD__
      name: _V_mask
      parent: V
      F: __STATE__B = FAILURE
      S: __STATE__B = SUCCESS
      template_type: t/condition
      children:
        - __V_mask_SR
        - __V_mask_FR
      view_children: ~
    __V_mask_FR:
      false_state: RUNNING
      type: condition
      parent: _V_mask
      true_state: FAILURE
      expr: __STATE__B = FAILURE
    __V_mask_SR:
      true_state: SUCCESS
      type: condition
      expr: __STATE__B = SUCCESS
      parent: _V_mask
      false_state: RUNNING
    A:
      type: condition
      parent: root
      expr: !<!> a > b
      false_state: R
      true_state: S
    root:
      children: [A, V]
      parent: !<!> ""
      type: sequence
    
    """

    yaml_code3 = """
__actions_latch_mask_FR: {expression: __STATE__actions == FAILURE, false_state: RUNNING,
  true_state: FAILURE, type: condition}
__actions_latch_mask_SR: {expression: __STATE__actions == SUCCESS, false_state: RUNNING,
  true_state: SUCCESS, type: condition}
__init_branch_if_reset_FR: {expression: reset_var == True, false_state: RUNNING, true_state: FAILURE,
  type: condition}
__init_branch_if_reset_SR: {expression: reset_var != True, false_state: RUNNING, true_state: SUCCESS,
  type: condition}
__some_latch_mask_FR: {expression: __STATE__some == FAILURE, false_state: RUNNING,
  true_state: FAILURE, type: condition}
__some_latch_mask_SR: {expression: __STATE__some == SUCCESS, false_state: RUNNING,
  true_state: SUCCESS, type: condition}
__test_latch_mask_FR: {expression: __STATE__test == FAILURE, false_state: RUNNING,
  true_state: FAILURE, type: condition}
__test_latch_mask_SR: {expression: __STATE__test == SUCCESS, false_state: RUNNING,
  true_state: SUCCESS, type: condition}
_actions_latch_mask:
  F: __STATE__actions == FAILURE
  S: __STATE__actions == SUCCESS
  children: [__actions_latch_mask_SR, __actions_latch_mask_FR]
  parent: actions_latch
  type: skipper
  view:
    F: __STATE__actions == FAILURE
    S: __STATE__actions == SUCCESS
    children: []
_init_branch_check_if_reset:
  children: [_init_branch_if_reset, _init_branch_reset_children_and_set_var_back]
  type: fallback
_init_branch_if_reset:
  F: reset_var == True
  S: reset_var != True
  children: [__init_branch_if_reset_SR, __init_branch_if_reset_FR]
  type: skipper
  view:
    F: reset_var == True
    S: reset_var != True
    children: []
_init_branch_reset_children:
  children: [some_reset_action, test_reset_action, actions_reset_action]
  type: sequence
_init_branch_reset_children_and_set_var_back:
  children: [_init_branch_reset_children, _init_branch_set_var_back]
  type: sequence
_init_branch_seq_w_latches:
  children: [some_latch, test_latch, actions_latch]
  control_type: sequence
  type: sequence
  view:
    children: [some, test, actions]
_init_branch_set_var_back: {script: reset_var = False, type: action}
_some_latch_mask:
  F: __STATE__some == FAILURE
  S: __STATE__some == SUCCESS
  children: [__some_latch_mask_SR, __some_latch_mask_FR]
  parent: some_latch
  type: skipper
  view:
    F: __STATE__some == FAILURE
    S: __STATE__some == SUCCESS
    children: []
_test_latch_mask:
  F: __STATE__test == FAILURE
  S: __STATE__test == SUCCESS
  children: [__test_latch_mask_SR, __test_latch_mask_FR]
  parent: test_latch
  type: skipper
  view:
    F: __STATE__test == FAILURE
    S: __STATE__test == SUCCESS
    children: []
actions: {script: test_str += 'actions! (these actions done only once!)', type: action}
actions_latch:
  child: actions
  children: [_actions_latch_mask, actions]
  type: skipper
  view:
    children: [actions]
actions_reset_action: {script: __STATE__actions = RUNNING;, type: action}
check_me: {script: test_str = 'Hey! ', type: action}
env_branch: {script: ENV = 'ROS_SIM', type: action}
init_branch:
  children: [_init_branch_check_if_reset, _init_branch_seq_w_latches]
  control_type: sequence
  reset_var: reset_var
  type: sequence
  view:
    children: [some, test, actions]
    reset: reset_var
root:
  children: [env_branch, check_me, init_branch]
  root: true
  type: sequence
some: {script: test_str += 'some ', type: action}
some_latch:
  child: some
  children: [_some_latch_mask, some]
  type: skipper
  view:
    children: [some]
some_reset_action: {script: __STATE__some = RUNNING;, type: action}
test: {script: test_str += 'test ', type: action}
test_latch:
  child: test
  children: [_test_latch_mask, test]
  type: skipper
  view:
    children: [test]
test_reset_action: {script: __STATE__test = RUNNING;, type: action}
    
    
    """

    d = DotCoder()
    d.tree_from_yaml(yaml_code3)
    print(d.get_dotcode())
