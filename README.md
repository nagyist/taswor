# taswor
Task Workflow creates the possibility to create, manage and visualize complex workflows.

This is a basic example of what I wish to accomplish

```python

    def func1():
        return Next("middle_node")
        
    def func2():
        return Next("leaf_node", 1)
        
    def func3(number):
        Storage.put("result", number)
        
    workflow = Workflow(
        Node(func=func1, start=True, name="start_node"),
        Node(func=func2, name="middle_node"),
        Node(func=func3, name="leaf_node")
    )
    workflow.process()

```
