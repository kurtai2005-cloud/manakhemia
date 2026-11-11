extends ConditionLeaf
class_name BtCond
## 用 Callable 包一條條件（Beehave ConditionLeaf）。

var fn: Callable


func tick(actor: Node, blackboard: Blackboard) -> int:
	if fn.is_valid() and bool(fn.call(actor, blackboard)):
		return SUCCESS
	return FAILURE
