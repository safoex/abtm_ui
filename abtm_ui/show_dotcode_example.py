from abtm_ui.start import ABTMApp
import time


yml = """
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

if __name__ == '__main__':
    app = ABTMApp()

    app.setup_all(with_ros=False)

    time.sleep(0.1)

    msg = {'data': yml}

    app.on_tree(msg)

    app.run()