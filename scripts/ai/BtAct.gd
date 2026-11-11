extends ActionLeaf
class_name BtAct
## 用 Callable 包一個動作（Beehave ActionLeaf）。fn 回 SUCCESS／FAILURE／RUNNING。

var fn: Callable


func tick(actor: Node, blackboard: Blackboard) -> int:
	if fn.is_valid():
		var r: Variant = fn.call(actor, blackboard)
		if r is int:
			return r
		return SUCCESS if bool(r) else FAILURE
	return FAILURE
