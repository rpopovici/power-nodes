import bpy
from bpy.props import StringProperty, BoolProperty, FloatVectorProperty, IntProperty
from bpy.types import NodeTree, NodeSocket, NodeSocketStandard


def should_ignore(node):
    return node.bl_idname in ['NodeGroupInput', 'NodeGroupOutput', 'NodeFrame', 'NodeReroute']


def process_node(node=None, process_flag=False, display_flag=True):
    if should_ignore(node):
        return
    # make sure node has state updated before processing
    node._update()
    node.needs_update = False

    p_flag = process_flag
    d_flag = display_flag
    if node and hasattr(node, "process"):
        if node.needs_processing or p_flag:
            # mark all of them downstream
            p_flag = True
            node.process()
        if node.needs_display:
            # display only the node marked for display
            d_flag = False
        # display always after processing
        node.display(node.needs_display and display_flag)
        # if node.is_active:
        #     return
        next_nodes = [link.to_node for output in node.outputs for link in output.links]
        for next_node in next_nodes:
            # waterfall events
            process_node(next_node, p_flag, d_flag)


def process_tree(ng=None):
    for node in ng.trigger_nodes:
        process_node(node)


class NodeTreeBase(object):
    needs_update : BoolProperty(default=False)
    trigger_nodes = []
    invalid_links = set()

    show_preview : BoolProperty(default=True)


    def build_update_list(self):
        self.trigger_nodes = [node for node in self.nodes if not should_ignore(node) and (node.needs_processing or node.needs_display or node.it_displays)]


        group_input_nodes = [node for node in self.nodes if node.bl_idname == 'NodeGroupInput']
        for node in group_input_nodes:
            for socket in node.inputs:
                if socket.is_linked:
                    other = socket.other
                    other.node.needs_processing = True
                    self.trigger_nodes.append(other.node)


    def remove_invalid_links(self):
        try:
            for inv_link in self.invalid_links.copy():
                self.links.remove(inv_link)
                self.invalid_links.discard(inv_link)
        except Exception as e:
            print('Failed to remove link: ', str(e))


    def force_update_on_external_events(self):
        if hasattr(bpy.context, "active_operator") and bpy.context.active_operator is not None:
            if bpy.context.active_operator.bl_idname in ['NODE_OT_links_cut']: # 'NODE_OT_translate_attach'
                for node in self.nodes:
                    node.needs_processing = True


    def evaluate_drivers(self):
        if self.animation_data is None:
            return

        for fcurve in self.animation_data.drivers:
            data_path_fixed = '.'.join(fcurve.data_path.split('.')[:-1])
            target_id = self.path_resolve(data_path_fixed)

            current_value = target_id['prop'][fcurve.array_index] if target_id.bl_rna.properties['prop'].array_length > 0 else target_id['prop']
            evaluated_value = self.path_resolve(fcurve.driver.variables[0].targets[0].data_path)
            # evalated_value = evaluated_id[fcurve.array_index] if evaluated_id.bl_rna.properties['prop'].array_length > 0 else evaluated_id
            # evaluated = fcurve.evaluate(bpy.context.scene.frame_current)
            if current_value != evaluated_value:
                if target_id.bl_rna.properties['prop'].array_length > 0:
                    target_id['prop'][fcurve.array_index] = evaluated_value
                else:
                    target_id['prop'] = evaluated_value
                target_id.node.update_from_socket(target_id, bpy.context)

            # print(fcurve.evaluate(bpy.context.scene.frame_current))
            # fcurve.update()


    def update_frame(self):
        # handle injected nodes
        if '_pn_node_hooks_' in self:
            hooks = self['_pn_node_hooks_']
            for hook, node_paths in hooks.items():
                if hook == '$FRAME':
                    for node_path in node_paths:
                        node = eval(node_path)
                        if node:
                            node.needs_processing = True
                            node._update()

        if not self.animation_data:
            return

        for fcurve in self.animation_data.action.fcurves:
            data_path_fixed = '.'.join(fcurve.data_path.split('.')[:-1])
            target_id = self.path_resolve(data_path_fixed)

            current_value = target_id['prop'][fcurve.array_index] if target_id.bl_rna.properties['prop'].array_length > 0 else target_id['prop']
            # evalated_value = evaluated_id[fcurve.array_index] if evaluated_id.bl_rna.properties['prop'].array_length > 0 else evaluated_id
            # evaluated = self.path_resolve(fcurve.driver.variables[0].targets[0].data_path)
            evaluated_value = fcurve.evaluate(bpy.context.scene.frame_current)
            if current_value != evaluated_value:
                if target_id.bl_rna.properties['prop'].array_length > 0:
                    target_id['prop'][fcurve.array_index] = evaluated_value
                else:
                    target_id['prop'] = evaluated_value
                target_id.node.update_from_socket(target_id, bpy.context)

            # print(fcurve.evaluate(bpy.context.scene.frame_current))
            # fcurve.update()
            for keyframe in fcurve.keyframe_points:
                pass

        for track in self.animation_data.nla_tracks:
            for strip in track.strips:
                print(strip.action)
                action=strip.action

                for fcu in action.fcurves:
                    print(fcu.data_path + " channel " + str(fcu.array_index))
                    for keyframe in fcu.keyframe_points:
                        print(keyframe.co)

        self.update_tag()


class PowerTree(NodeTree, NodeTreeBase):
    ''' Power nodes tree '''

    bl_idname = 'PowerTree'

    bl_label = 'Power Nodes'

    bl_icon = 'NODETREE'

    bl_description = 'Power Nodes'

    @classmethod
    def poll(cls, context):
        return True

    def interface_update(context):
        pass

    def update(self):
        self.remove_invalid_links()
        self.evaluate_drivers()
        self.force_update_on_external_events()

        self.needs_update = True
        # force update is needed in some cases
        self.update_tag()
        # bpy.context.view_layer.update()


    def process(self):
        if self.needs_update:
            self.needs_update = False
            self.build_update_list()
            process_tree(self)
