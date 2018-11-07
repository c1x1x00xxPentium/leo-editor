# -*- coding: utf-8 -*-
#@+leo-ver=5-thin
#@+node:ekr.20181103094900.1: * @file leoflexx.py
#@@first
#@@language python
#@@tabwidth -4
'''
A Stand-alone prototype for Leo using flexx.
'''
import leo.core.leoBridge as leoBridge
from flexx import flx
#@+others
#@+node:ekr.20181103151350.1: **  init
def init():
    # At present, leoflexx is not a true plugin.
    # I am executing leoflexx.py from an external script.
    return False
#@+node:ekr.20181106133100.1: **  lpad & rpad
# pscript does not support alignment, like %20s, in string formatting.

def lpad(s, width=0):
    '''Return s padded to the left.'''
    padding = max(0, width-len(s))
    return ' '*padding + s
    
def rpad(s, width=0):
    '''Return s padded to the right.'''
    padding = max(0, width-len(s))
    return s + ' '*padding
#@+node:ekr.20181107053436.1: ** Py side: flx.PyComponents
#@+node:ekr.20181107052522.1: *3* class LeoApp
class LeoApp(flx.PyComponent):
    '''
    The Leo Application.
    This is self.root for all flx.Widget objects!
    '''
    gui = flx.AnyProp(settable=True)
    main_window = flx.AnyProp(settable=True)

    # https://github.com/flexxui/flexx/issues/489
    def init(self):
        # This code does *not* call the init methods!
        gui = LeoGui()
        self._mutate_gui(gui)
        main_window = LeoMainWindow(gui.body, gui.outline)
        self._mutate_main_window(main_window)
        
    # @flx.action
    # def set_main_window(self, main_window):
        # print('app.set_main_window: main_window', main_window)
        # self._mutate_main_window(main_window)

#@+node:ekr.20181104174357.1: *3* class LeoGui
class LeoGui (flx.PyComponent):
    '''A class representing Leo's Browser gui.'''
    
    body = flx.StringProp('<Empty body>', settable=True)
    outline = flx.ListProp(['<Empty outline>'], settable=True)
    
    def init(self):
        self.c, self.g = self.open_bridge()
        self._mutate_body(self.find_body())
        self._mutate_outline(self.get_outline_list())

    #@+others
    #@+node:ekr.20181106070704.1: *4* gui.runMainLoop
    def runMainLoop(self):
        '''The main loop for the flexx gui.'''
    #@+node:ekr.20181105091545.1: *4* gui.open_bridge
    def open_bridge(self):
        '''Can't be in JS.'''
        bridge = leoBridge.controller(gui = None,
            loadPlugins = False,
            readSettings = False,
            silent = False,
            tracePlugins = False,
            verbose = False, # True: prints log messages.
        )
        if not bridge.isOpen():
            print('Error opening leoBridge')
            return
        g = bridge.globals()
        path = g.os_path_finalize_join(g.app.loadDir, '..', 'core', 'LeoPy.leo')
        if not g.os_path_exists(path):
            print('open_bridge: does not exist:', path)
            return
        c = bridge.openLeoFile(path)
        ### runUnitTests(c, g)
        return c, g
    #@+node:ekr.20181105160448.1: *4* gui.find_body
    def find_body(self):
        
        c = self.c
        for p in c.p.self_and_siblings():
            if p.b.strip():
                return p.b
        return ''
    #@+node:ekr.20181105095150.1: *4* gui.get_outline_list
    def get_outline_list(self):
        '''
        Return a serializable representation of the outline for the LeoTree
        class.
        '''
        c = self.c
        return [(p.archivedPosition(), p.gnx, p.h) for p in c.all_positions()]
    #@-others
#@+node:ekr.20181107052700.1: ** Js side: flx.Widgets
#@+node:ekr.20181104082144.1: *3* class LeoBody
base_url = 'https://cdnjs.cloudflare.com/ajax/libs/ace/1.2.6/'
flx.assets.associate_asset(__name__, base_url + 'ace.js')
flx.assets.associate_asset(__name__, base_url + 'mode-python.js')
flx.assets.associate_asset(__name__, base_url + 'theme-solarized_dark.js')

class LeoBody(flx.Widget):
    
    """ A CodeEditor widget based on Ace.
    """

    CSS = """
    .flx-CodeEditor > .ace {
        width: 100%;
        height: 100%;
    }
    """

    def init(self, body):
        global window
        self.ace = window.ace.edit(self.node, "editor")
        self.ace.setValue(body)
            # Trying to access global body yields:
            # JS: TypeError: e.match is not a function
        self.ace.navigateFileEnd()  # otherwise all lines highlighted
        self.ace.setTheme("ace/theme/solarized_dark")
        self.ace.getSession().setMode("ace/mode/python")

    @flx.reaction('size')
    def __on_size(self, *events):
        self.ace.resize()
#@+node:ekr.20181104082149.1: *3* class LeoLog
class LeoLog(flx.Widget):

    CSS = """
    .flx-CodeEditor > .ace {
        width: 100%;
        height: 100%;
    }
    """

    def init(self):
        global window
        self.ace = window.ace.edit(self.node, "editor")
        self.ace.navigateFileEnd()  # otherwise all lines highlighted
        # pscript.RawJS('''
            # var el = $(the_element);
            # var editor = el.data('ace').editor;
            # editor.$blockScrolling = Infinity;
        # ''')
        self.ace.setTheme("ace/theme/solarized_dark")
        
    def put(self, s):
        self.ace.setValue(self.ace.getValue() + '\n' + s)

    @flx.reaction('size')
    def __on_size(self, *events):
        self.ace.resize()
#@+node:ekr.20181104082130.1: *3* class LeoMainWindow
class LeoMainWindow(flx.Widget):
    
    ###
        # def __init__(self, *init_args, **kwargs):
            # # Inject the leo_outline *property*.
            # self.leo_body = kwargs ['body']
            # del kwargs ['body']
            # self.leo_outline = kwargs ['outline']
            # del kwargs ['outline']
            # super().__init__(*init_args, **kwargs)

    def init(self, body, outline):
        with flx.VBox():
            with flx.HBox(flex=1):
                self.tree = LeoTree(outline, flex=1)
                self.log = LeoLog(flex=1)
            self.body = LeoBody(body, flex=1)
            self.minibuffer = LeoMiniBuffer()
            self.status_line = LeoStatusLine()
#@+node:ekr.20181104082154.1: *3* class LeoMiniBuffer
class LeoMiniBuffer(flx.Widget):
    
    def init(self): 
        with flx.HBox():
            flx.Label(text='Minibuffer')
            self.widget = flx.LineEdit(
                flex=1, placeholder_text='Enter command')
        self.widget.apply_style('background: yellow')
#@+node:ekr.20181104082201.1: *3* class LeoStatusLine
class LeoStatusLine(flx.Widget):
    
    def init(self):
        with flx.HBox():
            flx.Label(text='Status Line')
            self.widget = flx.LineEdit(flex=1, placeholder_text='Status')
        self.widget.apply_style('background: green')
#@+node:ekr.20181104082138.1: *3* class LeoTree
class LeoTree(flx.Widget):

    CSS = '''
    .flx-TreeWidget {
        background: #000;
        color: white;
        /* background: #ffffec; */
        /* Leo Yellow */
        /* color: #afa; */
    }
    '''

    def init(self, outline):
        print('LeoTree.root', repr(self.root))
        with flx.TreeWidget(flex=1, max_selected=1) as self.tree:
            self.make_tree(outline)

    #@+others
    #@+node:ekr.20181105045657.1: *4* tree.make_tree
    def make_tree(self, outline):

        stack = []
        for archived_position, gnx, h in outline:
            n = len(archived_position)
            if n == 1:
                item = flx.TreeItem(text=h, checked=None, collapsed=True)
                stack = [item]
            elif n in (2, 3):
                # Fully expanding the stack takes too long.
                stack = stack[:n-1]
                with stack[-1]:
                    item = flx.TreeItem(text=h, checked=None, collapsed=True)
                    stack.append(item)
    #@+node:ekr.20181104080854.3: *4* tree.on_event
    @flx.reaction(
        'tree.children**.checked',
        'tree.children**.selected',
        'tree.children**.collapsed',
    )
    def on_event(self, *events):
        
        for ev in events:
            id_ = ev.source.title or ev.source.text
            kind = '' if ev.new_value else 'un-'
            s = kind + ev.type
            assert s, id_
            self.root.main_window.log.put('%s: %s' % (lpad(s, 15), id_))
    #@-others
#@-others
if __name__ == '__main__':
    flx.launch(LeoApp, runtime='firefox-browser')
    print('After flx.launch')
    flx.run()
#@-leo
