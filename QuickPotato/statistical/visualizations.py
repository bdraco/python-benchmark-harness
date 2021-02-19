from QuickPotato.database.queries import Crud
from QuickPotato.utilities.html_templates import flame_graph_template
from QuickPotato.utilities.defaults import default_test_case_name
from jinja2 import Template


class FlameGraph(Crud):

    def __init__(self, test_case_name=default_test_case_name, test_id=None):
        """
        When initialized it will generate a hieratical json stack for each sample
        in the test id attached to the specified test case and make it possible to render D3-flame-graphs.
        For more info about D3-flame-graphs visit:

        https://github.com/spiermar/d3-flame-graph

        :param test_case_name: The name of the test case (This is also always the database name).
                               If test case name is not defined it will default to the quick profiling
                               database/test case name.
        :param test_id: The generated test id, if it is not defined and the test case is rolled to
                        default the latest available test id wil be used.
        """
        super(FlameGraph, self).__init__()

        if test_id is None and test_case_name == default_test_case_name:
            test_id = self.select_test_ids_with_performance_statistics(database=test_case_name)[-1]

        else:
            raise FileNotFoundError  # <-- Create better error

        self.list_of_samples = self.select_all_sample_ids(test_case_name, test_id)
        self._current_number_of_children = 0

        self.json = [self._discover_relationships(test_case_name, sample) for sample in self.list_of_samples]
        self.html = self._render_html()

    def _render_html(self):
        """
        Renders a HTML web page that contains the flame graph.
        :return: A filled in HTML template
        """
        template = Template(flame_graph_template)
        return template.render(
            list_of_samples=self.list_of_samples,
            payload=self.json,
        )

    def _recursively_update_parent_child_relationship(self, stack, parent, child):
        """
        Helps map out the call stack by extending or updating the
        hierarchical stack with new members.

        (Function is recursive until there are no more objects in the stack.)

        :param stack: The hierarchical JSON call stack.
        :param parent: The name of the parent function.
        :param child: The name of the child function.
        """
        if stack['name'] == parent:
            stack['children'].append(
                {
                    "name": child,
                    "children": []
                }
            )

        else:
            for item in stack['children']:
                self._recursively_update_parent_child_relationship(item, parent, child)

    def _recursively_count_samples(self, stack, function_name):
        """
        Will count how many children/samples the given function name has.

        (Function is recursive and will travel through the hierarchical
        JSON stack until no more member can be found.)

        :param stack: The discovered hierarchical JSON call stack without the amount of samples.
        :param function_name: The name of the member function
        """
        self._current_number_of_children += 1 if len(stack['children']) == 0 else len(stack['children'])
        for relationship in stack["children"]:
            self._recursively_count_samples(relationship, function_name)

    def _count_relationships(self, stack):
        """
        Will travel down the discovered hierarchical stack and add the amount of samples per member.

        (Function is recursive and will travel through the hierarchical
        JSON stack until no more member can be found.)

        :param stack: The discovered hierarchical JSON call stack without the amount of samples.
        :return: The discovered hierarchical JSON call with the amount of samples per member.
        """
        self._recursively_count_samples(stack, stack["name"])
        stack['value'] = self._current_number_of_children
        self._current_number_of_children = 0
        for relationship in stack["children"]:
            self._count_relationships(relationship)
        return stack

    def _discover_relationships(self, test_case_name, sample_id):
        """
        Will map out the parent child relationships for each function to form hierarchical data structure.
        This structure can than be used to generate D3 flame graphs.

        (Function uses recursion to travel through the hierarchical
        JSON stack until no more row in the collected stack trace can be found.)

        :return: An hierarchical data structure in JSON format.
        """
        stack = {}
        collected_stack_trace = self.select_call_stack_by_sample_id(test_case_name, sample_id)
        for line in collected_stack_trace:

            if line["parent_function_name"] == collected_stack_trace[0]['parent_function_name']:
                stack["name"] = line["parent_function_name"]
                stack["children"] = [
                    {
                        "name": line["child_function_name"],
                        "children": []
                    }
                ]

            else:
                self._recursively_update_parent_child_relationship(
                    stack=stack,
                    parent=line['parent_function_name'],
                    child=line['child_function_name']
                )
        return self._count_relationships(stack)
