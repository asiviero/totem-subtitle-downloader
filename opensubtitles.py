# -*- coding: utf-8 -*-

from gi.repository import Peas
from gi.repository import Gtk
from gi.repository import Gdk
from gi.repository import Gio
from gi.repository import Pango
from gi.repository import Totem
from gi.repository import GObject

import xmlrpclib
import threading
import xdg.BaseDirectory
from os import sep, path, mkdir,rename
import gettext

from hash import hashFile

gettext.textdomain("totem")

D_ = gettext.dgettext
_ = gettext.gettext

GObject.threads_init()

USER_AGENT = 'Totem'
OK200 = '200 OK'
TOTEM_REMOTE_COMMAND_REPLACE = 14

SUBTITLES_EXT = [
	"asc",
	"txt",
        "sub",
        "srt",
        "smi",
        "ssa",
        "ass",
]

# Map of the language codes used by opensubtitles.org's API to their human-readable name
LANGUAGES_STR = [(D_('iso_639_3', 'Albanian'), 'sq'),
		 (D_('iso_639_3', 'Arabic'), 'ar'),
		 (D_('iso_639_3', 'Armenian'), 'hy'),
		 (D_('iso_639_3', 'Neo-Aramaic, Assyrian'), 'ay'),
		 (D_('iso_639_3', 'Bosnian'), 'bs'),
		 (_('Brasilian Portuguese'), 'pb'),
		 (D_('iso_639_3', 'Bulgarian'), 'bg'),
		 (D_('iso_639_3', 'Catalan'), 'ca'),
		 (D_('iso_639_3', 'Chinese'), 'zh'),
		 (D_('iso_639_3', 'Croatian'), 'hr'),
		 (D_('iso_639_3', 'Czech'), 'cs'),
		 (D_('iso_639_3', 'Danish'), 'da'),
		 (D_('iso_639_3', 'Dutch'), 'nl'),
		 (D_('iso_639_3', 'English'), 'en'),
		 (D_('iso_639_3', 'Esperanto'), 'eo'),
		 (D_('iso_639_3', 'Estonian'), 'et'),
		 (D_('iso_639_3', 'Finnish'), 'fi'),
		 (D_('iso_639_3', 'French'), 'fr'),
		 (D_('iso_639_3', 'Galician'), 'gl'),
		 (D_('iso_639_3', 'Georgian'), 'ka'),
		 (D_('iso_639_3', 'German'), 'de'),
		 (D_('iso_639_3', 'Greek, Modern (1453-)'), 'el'),
		 (D_('iso_639_3', 'Hebrew'), 'he'),
		 (D_('iso_639_3', 'Hindi'), 'hi'),
		 (D_('iso_639_3', 'Hungarian'), 'hu'),
		 (D_('iso_639_3', 'Icelandic'), 'is'),
		 (D_('iso_639_3', 'Indonesian'), 'id'),
		 (D_('iso_639_3', 'Italian'), 'it'),
		 (D_('iso_639_3', 'Japanese'), 'ja'),
		 (D_('iso_639_3', 'Kazakh'), 'kk'),
		 (D_('iso_639_3', 'Korean'), 'ko'),
		 (D_('iso_639_3', 'Latvian'), 'lv'),
		 (D_('iso_639_3', 'Lithuanian'), 'lt'),
		 (D_('iso_639_3', 'Luxembourgish'), 'lb'),
		 (D_('iso_639_3', 'Macedonian'), 'mk'),
		 (D_('iso_639_3', 'Malay (macrolanguage)'), 'ms'),
		 (D_('iso_639_3', 'Norwegian'), 'no'),
		 (D_('iso_639_3', 'Occitan (post 1500)'), 'oc'),
		 (D_('iso_639_3', 'Persian'), 'fa'),
		 (D_('iso_639_3', 'Polish'), 'pl'),
		 (D_('iso_639_3', 'Portuguese'), 'pt'),
		 (D_('iso_639_3', 'Romanian'), 'ro'),
		 (D_('iso_639_3', 'Russian'), 'ru'),
		 (D_('iso_639_3', 'Serbian'), 'sr'),
		 (D_('iso_639_3', 'Slovak'), 'sk'),
		 (D_('iso_639_3', 'Slovenian'), 'sl'),
		 (D_('iso_639_3', 'Spanish'), 'es'),
		 (D_('iso_639_3', 'Swedish'), 'sv'),
		 (D_('iso_639_3', 'Thai'), 'th'),
		 (D_('iso_639_3', 'Turkish'), 'tr'),
		 (D_('iso_639_3', 'Ukrainian'), 'uk'),
		 (D_('iso_639_3', 'Vietnamese'), 'vi'),]

# Map of ISO 639-1 language codes to the codes used by opensubtitles.org's API
LANGUAGES =     {'sq':'alb',
		 'ar':'ara',
		 'hy':'arm',
		 'ay':'ass',
		 'bs':'bos',
		 'pb':'pob',
		 'bg':'bul',
		 'ca':'cat',
		 'zh':'chi',
		 'hr':'hrv',
		 'cs':'cze',
		 'da':'dan',
		 'nl':'dut',
		 'en':'eng',
		 'eo':'epo',
		 'et':'est',
		 'fi':'fin',
		 'fr':'fre',
		 'gl':'glg',
		 'ka':'geo',
		 'de':'ger',
		 'el':'ell',
		 'he':'heb',
		 'hi':'hin',
		 'hu':'hun',
		 'is':'ice',
		 'id':'ind',
		 'it':'ita',
		 'ja':'jpn',
		 'kk':'kaz',
		 'ko':'kor',
		 'lv':'lav',
		 'lt':'lit',
		 'lb':'ltz',
		 'mk':'mac',
		 'ms':'may',
		 'no':'nor',
		 'oc':'oci',
		 'fa':'per',
		 'pl':'pol',
		 'pt':'por',
		 'ro':'rum',
		 'ru':'rus',
		 'sr':'scc',
		 'sk':'slo',
		 'sl':'slv',
		 'es':'spa',
		 'sv':'swe',
		 'th':'tha',
		 'tr':'tur',
		 'uk':'ukr',
		 'vi':'vie',}

# Option to download by hash or filename
DOWNLOAD_BY_HASH = 0;
DOWNLOAD_BY_FILENAME = 1;

class SearchThread(threading.Thread):
    """
    This is the thread started when the dialog is searching for subtitles
    """
    def __init__(self, model):
        self.model = model
        self._done = False
        self._lock = threading.Lock()
        threading.Thread.__init__(self)

    def run(self):
        self.model.lock.acquire(True)
        self.model.results = self.model.os_search_subtitles()
        self.model.lock.release()
        self._done = True
	
    @property
    def done(self):
        """ Thread-safe property to know whether the query is done or not """
        self._lock.acquire(True)
        res = self._done
        self._lock.release()
        return res

class DownloadThread(threading.Thread):
    """
    This is the thread started when the dialog is downloading the subtitles.
    """
    def __init__(self, model, subtitle_id):
        self.model = model
        self.subtitle_id = subtitle_id
        self._done = False
        self._lock = threading.Lock()
        threading.Thread.__init__(self)

    def run(self):
        self.model.lock.acquire(True)
        self.model.subtitles = self.model.os_download_subtitles(self.subtitle_id)
        self.model.lock.release()
        self._done = True
    
    @property
    def done(self):
        """ Thread-safe property to know whether the query is done or not """
        self._lock.acquire(True)
        res = self._done
        self._lock.release()
        return res

# OpenSubtitles.org API abstraction

class OpenSubtitlesModel(object):
    """
    This contains the logic of the opensubtitles service.
    """
    def __init__(self, server):
        self.server = server
        self.token = None

        try:
            import locale
            self.lang = LANGUAGES[locale.getlocale()[0].split('_')[0]]
        except:
            self.lang = 'eng'
        self.hash = None
        self.size = 0

        self.lock = threading.Lock()
        self.results = []
        self.subtitles = ''

        self.message = ''

    def os_login(self, username='', password=''):
        """
        Logs into the opensubtitles web service and gets a valid token for
        the comming comunications. If we are already logged it only checks
        the if the token is still valid.

        @rtype : bool
        """
        result = None
        self.message = ''

        if self.token:
            # We have already logged-in before, check the connection
            try:
                result = self.server.NoOperation(self.token)
            except:
                pass
            if result and result['status'] != OK200:
                return True
        try:
            result = self.server.LogIn(username, password, self.lang, USER_AGENT)
        except:
            pass
        if result and result.get('status') == OK200:
            self.token = result.get('token')
            if self.token:
                return True

        self.message = _(u'Could not contact the OpenSubtitles website')

        return False

    def os_search_subtitles(self):
        """

        """
        self.message = ''
        if self.os_login():
	    if(self.hash_or_filename == DOWNLOAD_BY_HASH) :	    	
	            searchdata = {'sublanguageid': self.lang,
	                          'moviehash'    : self.hash, 
                          	  'moviebytesize': str(self.size)}
	    elif(self.hash_or_filename == DOWNLOAD_BY_FILENAME) :
	            searchdata = {'sublanguageid': self.lang,
	                          'query' : self.filename}
            try:
                result = self.server.SearchSubtitles(self.token, [searchdata])
            except xmlrpclib.ProtocolError:
                self.message = _(u'Could not contact the OpenSubtitles website')

            if result.get('data'):
                return result['data']
            else:
                self.message = _(u'No results found')

        return None

    def os_download_subtitles(self, subtitleId):
        """
        """
        self.message = ''
        if self.os_login():
            try:
                result = self.server.DownloadSubtitles(self.token, [subtitleId])
            except xmlrpclib.ProtocolError:
                self.message = _(u'Could not contact the OpenSubtitles website')

            if result and result.get('status') == OK200:
                try:
                    subtitle64 = result['data'][0]['data']
                except:
                    self.message = _(u'Could not contact the OpenSubtitles website')
                    return None

                import StringIO, gzip, base64
                subtitleDecoded = base64.decodestring(subtitle64)
                subtitleGzipped = StringIO.StringIO(subtitleDecoded)
                subtitleGzippedFile = gzip.GzipFile(fileobj=subtitleGzipped)

                return subtitleGzippedFile.read()

        return None

class OpenSubtitles(GObject.Object, Peas.Activatable):
    __gtype_name__ = 'OpenSubtitles'

    object = GObject.property(type = GObject.Object)

    def __init__(self):
        GObject.Object.__init__ (self)

        self.dialog = None
        self.totem = None
        self.settings = Gio.Settings.new ('org.gnome.totem.plugins.opensubtitles')

    # totem.Plugin methods

    def do_activate(self):
        """
        Called when the plugin is activated.
        Here the sidebar page is initialized(set up the treeview, connect 
        the callbacks, ...) and added to totem.
        """
        self.totem = self.object
	self.filename = None

        self.manager = self.totem.get_ui_manager()
        self.os_append_menu()

        self.totem.connect('file-opened', self.on_totem__file_opened)
        self.totem.connect('file-closed', self.on_totem__file_closed)

	# Obtain the ServerProxy and init the model
        server = xmlrpclib.Server('http://api.opensubtitles.org/xml-rpc')
        self.model = OpenSubtitlesModel(server)

    def do_deactivate(self):
        if self.dialog:
            self.dialog.destroy()
	    self.dialog = None
	
        self.os_delete_menu()

    # UI related code

    def os_build_dialog(self, action):
        builder = Totem.plugin_load_interface ("opensubtitles", "opensubtitles.ui", True, self.totem.get_main_window(), None)

        # Obtain all the widgets we need to initialize
        combobox =       builder.get_object('language_combobox')
        languages =      builder.get_object('language_model')
       	hash_or_title_combobox = builder.get_object('file_hash_title')
        hash_filename_model = builder.get_object('hash_filename_model');
        save_same_location_select = builder.get_object('save_same_location');
        self.save_same_location = True;
        self.progress =  builder.get_object('progress_bar')
        self.treeview =  builder.get_object('subtitle_treeview')
        self.liststore = builder.get_object('subtitle_model')
        self.dialog =    builder.get_object('subtitles_dialog')
	self.find_button = builder.get_object('find_button')
	self.apply_button = builder.get_object('apply_button')
	self.close_button = builder.get_object('close_button')

        # Set up and populate the languages combobox
        renderer = Gtk.CellRendererText()
        sorted_languages = Gtk.TreeModelSort (model = languages)
        sorted_languages.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        combobox.set_model(sorted_languages)
        combobox.pack_start(renderer, True)
        combobox.add_attribute(renderer, 'text', 0)

        lang = self.settings.get_string ('language')
        if lang is not None:
            self.model.lang = lang

        for lang in LANGUAGES_STR:
            it = languages.append(lang)
            if LANGUAGES[lang[1]] == self.model.lang:
                (success, parentit) = sorted_languages.convert_child_iter_to_iter (it)
                if success:
                    combobox.set_active_iter (parentit)

	# Set up and populate hash or title option
	renderer = Gtk.CellRendererText()
	hash_or_title_combobox.pack_start(renderer, True)
	hash_or_title_combobox.add_attribute(renderer, 'text', 1)
	hash_or_title_model = Gtk.ListStore(int,str);
	hash_or_title_model.append([DOWNLOAD_BY_HASH,"Use Hash"]);
	hash_or_title_model.append([DOWNLOAD_BY_FILENAME,"Use Filename"]);
	hash_or_title_combobox.set_model(hash_or_title_model);
	hash_or_title_combobox.set_active(0);
	self.model.hash_or_filename = DOWNLOAD_BY_HASH;
	
        # Set up the results treeview 
        renderer = Gtk.CellRendererText()
        self.treeview.set_model(self.liststore)
        self.treeview.set_headers_visible(False)
        renderer.set_property('ellipsize', Pango.EllipsizeMode.END)
        column = Gtk.TreeViewColumn(_(u"Subtitles"), renderer, text=0)
        column.set_resizable(True)
        column.set_expand(True)
        self.treeview.append_column(column)
	# translators comment:
	# This is the file-type of the subtitle file detected
        column = Gtk.TreeViewColumn(_(u"Format"), renderer, text=1)
        column.set_resizable(False)
        self.treeview.append_column(column)
	# translators comment:
	# This is a rating of the quality of the subtitle
        column = Gtk.TreeViewColumn(_(u"Rating"), renderer, text=2)
        column.set_resizable(False)
        self.treeview.append_column(column)

	self.apply_button.set_sensitive(False)

        self.apply_button.connect('clicked', self.on_apply_clicked)
        self.find_button.connect('clicked', self.on_find_clicked)
        self.close_button.connect('clicked', self.on_close_clicked)

	# Set up signals

        combobox_changed_id = combobox.connect('changed', self.on_combobox__changed)
        hash_or_file_combobox_changed_id = hash_or_title_combobox.connect('changed',self.on_hash_or_filename_combobox__changed);
        save_same_location_select_changed_id = save_same_location_select.connect('toggled',self.on_save_same_select__changed);
	self.dialog.connect ('delete-event', self.dialog.hide_on_delete)
	self.dialog.set_transient_for (self.totem.get_main_window())
	self.dialog.set_position (Gtk.WindowPosition.CENTER_ON_PARENT)

	# Connect the callbacks
	self.dialog.connect ('key-press-event', self.on_window__key_press_event)
        self.treeview.get_selection().connect('changed', self.on_treeview__row_change)
        self.treeview.connect('row-activated', self.on_treeview__row_activate)

    def os_show_dialog(self, action):
        if not self.dialog:
            self.os_build_dialog(action)

        filename = self.totem.get_current_mrl()
        if not self.model.results or filename != self.filename:
            self.filename = filename

        self.dialog.show_all()

	self.progress.set_fraction(0.0)

    def os_append_menu(self):
        """
        """
	
        self.os_action_group = Gtk.ActionGroup(name='OpenSubtitles')

        self.action = Gtk.Action(name='opensubtitles',
                                 label=_(u'_Download Movie Subtitles…'),
                                 tooltip=_(u"Download movie subtitles from OpenSubtitles"),
                                 stock_id=None)

        self.os_action_group.add_action(self.action)

        self.manager.insert_action_group(self.os_action_group, 0)

        self.menu_id = self.manager.new_merge_id()
        self.manager.add_ui(self.menu_id,
                             '/tmw-menubar/view/subtitles/subtitle-download-placeholder',
                             'opensubtitles',
                             'opensubtitles',
                             Gtk.UIManagerItemType.MENUITEM,
                             False
                            )
        self.action.set_visible(True)

        self.manager.ensure_update()

        self.action.connect('activate', self.os_show_dialog)

        self.action.set_sensitive(self.totem.is_playing() and
				  self.os_check_allowed_scheme() and
                                  not self.os_check_is_audio())

    def os_check_allowed_scheme(self):
        scheme = Gio.file_new_for_uri(self.totem.get_current_mrl()).get_uri_scheme()
        if scheme == 'dvd' or scheme == 'http' or scheme == 'dvb' or scheme == 'vcd':
            return False
        return True

    def os_check_is_audio(self):
        # FIXME need to use something else here
        # I think we must use video widget metadata but I don't found a way 
	# to get this info from python
        filename = self.totem.get_current_mrl()
        if Gio.content_type_guess(filename, '')[0].split('/')[0] == 'audio':
            return True
        return False

    def os_delete_menu(self):
        self.manager.remove_action_group(self.os_action_group)
        self.manager.remove_ui(self.menu_id)

    def os_get_results(self):
        """
        """
        self.liststore.clear()
	self.treeview.set_headers_visible(False)
        self.model.results = []
        self.apply_button.set_sensitive(False)
	self.find_button.set_sensitive(False)        

        self.dialog.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))

        thread = SearchThread(self.model)
        thread.start()
        GObject.idle_add(self.os_populate_treeview)

        self.progress.set_text(_(u'Searching subtitles…'))
        GObject.timeout_add(350, self.os_progress_bar_increment, thread)

    def os_populate_treeview(self):
        """
        """
        if self.model.lock.acquire(False) == False:
            return True

        if self.model.results:
            self.apply_button.set_sensitive(True)
            for subData in self.model.results:
		if not SUBTITLES_EXT.count(subData['SubFormat']):
			continue
                self.liststore.append([subData['SubFileName'], subData['SubFormat'], subData['SubRating'], subData['IDSubtitleFile'],])
	        self.treeview.set_headers_visible(True)
        else:
            self.apply_button.set_sensitive(False)

        self.model.lock.release()

        self.dialog.get_window().set_cursor(None)

        return False

    def os_save_selected_subtitle(self, filename=None):
        """
        """
        self.dialog.get_window().set_cursor(Gdk.Cursor.new(Gdk.CursorType.WATCH))

        model, rows = self.treeview.get_selection().get_selected_rows()
        if rows:
            iter = model.get_iter(rows[0])
            subtitle_id = model.get_value(iter, 3)
            subtitle_format = model.get_value(iter, 1)

            gfile = None

            if not self.save_same_location:
                directory = Gio.file_new_for_path(xdg.BaseDirectory.xdg_cache_home + sep + 'totem' + sep + 'subtitles' + sep) 
                if not directory.query_exists(None):
                    if not path.exists (xdg.BaseDirectory.xdg_cache_home + sep + 'totem' + sep):
                        mkdir (xdg.BaseDirectory.xdg_cache_home + sep + 'totem' + sep)
                    if not path.exists (xdg.BaseDirectory.xdg_cache_home + sep + 'totem' + sep + 'subtitles' + sep):
                        mkdir (xdg.BaseDirectory.xdg_cache_home + sep + 'totem' + sep + 'subtitles' + sep)
                    # FIXME: We can't use this function until we depend on GLib (PyGObject) 2.18
                    # directory.make_directory_with_parents()

                file = Gio.file_new_for_path(self.filename)
                movie_name = file.get_basename().rpartition('.')[0]
                filename = directory.get_uri() + sep + movie_name + '.' + subtitle_format
            else :
            	# replace filename extension
		root, ext = path.splitext(filename)
		filename = root + "." + subtitle_format;
		
            self.model.subtitles = ''

            thread = DownloadThread(self.model, subtitle_id)
            thread.start()
            GObject.idle_add(self.os_save_subtitles, filename)

            self.progress.set_text(_(u'Downloading the subtitles…'))
            GObject.timeout_add(350, self.os_progress_bar_increment, thread)
        else:
            #warn user!
            pass

    def os_save_subtitles(self, filename):
        if self.model.lock.acquire(False) == False:
            return True

        if self.model.subtitles:
            # Delete all previous cached subtitle for this file 
            for ext in SUBTITLES_EXT:
		fp = Gio.file_new_for_path(filename[:-3] + ext)
		if fp.query_exists(None):
                    fp.delete(None)

            fp = Gio.file_new_for_uri (filename)
            suburi = fp.get_uri ()

            subFile = fp.replace ('', False, Gio.FileCreateFlags.REPLACE_DESTINATION, None)
            subFile.write (self.model.subtitles, None)
            subFile.close (None)

        self.model.lock.release()

        self.dialog.get_window().set_cursor(None)
        self.on_close_clicked (None)

        if suburi:
            self.totem.set_current_subtitle(suburi)

        return False

    def os_progress_bar_increment(self, thread):

        if not thread.done:
            self.progress.pulse()
            return True

        if self.model.message:
            self.progress.set_text(self.model.message)
        else:
            self.progress.set_text('')
	
	self.progress.set_fraction(0.0)
	self.find_button.set_sensitive(True)
        self.apply_button.set_sensitive(False)
        self.treeview.set_sensitive(True)
        return False

    def os_download_and_apply(self):
        self.apply_button.set_sensitive(False)
        self.find_button.set_sensitive(False)
        self.action.set_sensitive(False)
        self.treeview.set_sensitive(False)              
        self.os_save_selected_subtitle(self.filename)

    # Callbacks

    def on_window__key_press_event(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.dialog.destroy()
            self.dialog = None
            return True
        return False

    def on_treeview__row_change(self, selection):
        if selection.count_selected_rows() > 0:
            self.apply_button.set_sensitive(True)
        else:
            self.apply_button.set_sensitive(False)

    def on_treeview__row_activate(self, path, column, data):
	self.os_download_and_apply()

    def on_totem__file_opened(self, totem, filename):
        """
        """
        # Check if allows subtitles
	if self.os_check_allowed_scheme() and not self.os_check_is_audio():
            self.action.set_sensitive(True)
	    if self.dialog:
	    	self.find_button.set_sensitive(True)
		self.filename = self.totem.get_current_mrl()
		self.liststore.clear()
	        self.treeview.set_headers_visible(False)
	    	self.apply_button.set_sensitive(False)
		self.results = [] 
	else:
            self.action.set_sensitive(False)
	    if self.dialog and self.dialog.is_active():
                self.liststore.clear()
	        self.treeview.set_headers_visible(False)
	    	self.apply_button.set_sensitive(False)
	    	self.find_button.set_sensitive(False)

    def on_totem__file_closed(self, totem):
        self.action.set_sensitive(False)
        if self.dialog:
	    self.apply_button.set_sensitive(False)
	    self.find_button.set_sensitive(False)

    def on_combobox__changed(self, combobox):
        iter = combobox.get_active_iter()
        self.model.lang = LANGUAGES[combobox.get_model().get_value(iter, 1)]
        self.settings.set_string('language', self.model.lang)
        
    def on_hash_or_filename_combobox__changed(self, hash_or_file_combobox):
    	iter = hash_or_file_combobox.get_active_iter();
	self.model.hash_or_filename = hash_or_file_combobox.get_model().get_value(iter,0);
	
    def on_save_same_select__changed(self,select) :
    	self.save_same_location = select.get_active();

    def on_close_clicked(self, data):
        self.dialog.destroy()
        self.dialog = None

    def on_apply_clicked(self, data):
	self.os_download_and_apply()
	
    def on_find_clicked(self, data):
        self.apply_button.set_sensitive(False)
        self.find_button.set_sensitive(False)
        self.filename = self.totem.get_current_mrl()
        self.model.hash , self.model.size = hashFile(self.filename)
	self.model.filename = self.filename.split("/")[-1]
        self.os_get_results()

