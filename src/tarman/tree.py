import sys
sys.path.append("/home/matej/Dropbox/matej/workarea/pys/tarman/src")

from tarman.exceptions import NotFound
from tarman.exceptions import AlreadyExists
from tarman.exceptions import OutOfRange

import os
import stat


class Node():

    def __init__(self, data, parent=None, children=[]):
        self.parent = parent
        self.children = children
        self.data = data

    def add_child(self, data):
        tmp = Node(data=data, parent=self)
        if self.children:
            self.children += [tmp]
        else:
            self.children = [tmp]
        return tmp

    def __iter__(self):
        for child in self.children:
            if child.children:
                for c in child:
                    yield c
            else:
                yield child

    def get_array(self):
        result = []
        tmp = self
        while tmp != None:
            result = [tmp] + result
            tmp = tmp.parent
        return result

    def get_data_array(self):
        result = []
        tmp = self
        while tmp != None:
            result = [tmp.data] + result
            tmp = tmp.parent
        return result

    def __str__(self):
        return self.data

    def get_child(self, data):
        for c in self.children:
            if c.data == data:
                return c
        return None

    def del_self(self):
        if self.parent is None:
            return
        for i in range(len(self.parent.children)):
            if self.parent.children[i].data == self.data:
                del self.parent.children[i]
                return


class Tree():

    def __init__(self, root_data):
        self.root = Node(data=root_data, parent=None)


class FileNode(Node):

    def __init__(self, path, parent=None, sub=True):
        try:
            self.mode = os.stat(path).st_mode
            self.parent = parent
            if self.parent is None:
                self.data = path
            else:
                self.data = os.path.basename(path)
                for c in self.parent.children:
                    if self.data == c.data:
                        raise AlreadyExists(
                            "'{0}' is in '{1}'".format(self.data, path),
                            c
                        )
            self.children = []
            if self.is_dir() and sub:
                for n in os.listdir(path):
                    self.add_subdir(os.path.join(path, n))
        except OSError:
            raise NotFound(path)

    def is_dir(self):
        if stat.S_ISDIR(self.mode):
            return True
        else:
            return False

    def get_path(self):
        if self.parent:
            return os.path.join(*self.get_data_array())
        else:
            return self.data

    def add_subdir(self, path, parent=None, sub=True):
        parent = parent if parent else self
        try:
            tmp = FileNode(path, parent=self, sub=sub)
            if self.children:
                self.children += [tmp]
            else:
                self.children = [tmp]
            return tmp
        except AlreadyExists as e:
            return e.child  # self.add_subdir(path=path, parent=e.child, sub=sub)

    @staticmethod
    def _get_array_by_path(path):
        result = []
        prefix, name = os.path.split(path)
        while name:
            result = [name] + result
            prefix, name = os.path.split(prefix)
        return result

    def get_children_data(self):
        return [c.data for c in self.children]

    def __eq__(self, node):
        if node == self:
            return True

        if not isinstance(node, FileNode):
            return False

        f1 = self.get_path()
        f2 = node.get_path()

        return os.path.samefile(f1, f2)


class DirectoryTree(Tree):

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.root = FileNode(self.root_dir, sub=False)

    def __iter__(self):
        return self.root.__iter__()

    def add(self, path, sub=False):
        main_array = FileNode._get_array_by_path(self.root_dir)
        path_array = FileNode._get_array_by_path(path)

        d = self.root
        len_main = len(main_array)
        len_path = len(path_array)

        if len_main > len_path:
            raise OutOfRange(path)

        for i in range(len_main):
            if main_array[i] != path_array[i]:
                raise OutOfRange(path)

        for i in range(len_main, len_path - 1):
            d = d.add_subdir(
                os.path.join(d.get_path(), path_array[i]),
                sub=False
            )

        if len_main < len_path:
            d = d.add_subdir(
                    os.path.join(d.get_path(), path_array[i + 1]),
                    sub=sub
                )

        return d

    def __contains__(self, path):
        main_array = FileNode._get_array_by_path(self.root_dir)
        path_array = FileNode._get_array_by_path(path)

        d = self.root
        len_main = len(main_array)
        len_path = len(path_array)

        if len_main > len_path:
            raise OutOfRange(path)

        for i in range(len_main):
            if main_array[i] != path_array[i]:
                raise OutOfRange(path)

        for i in range(len_main, len_path):
            d = d.get_child(path_array[i])
            if d is None:
                return False

        return True

    def __getitem__(self, path):
        main_array = FileNode._get_array_by_path(self.root_dir)
        path_array = FileNode._get_array_by_path(path)

        d = self.root
        len_main = len(main_array)
        len_path = len(path_array)

        if len_main > len_path:
            raise OutOfRange(path)

        for i in range(len_main):
            if main_array[i] != path_array[i]:
                raise OutOfRange(path)

        for i in range(len_main, len_path):
            d = d.get_child(path_array[i])
            if d is None:
                return None
            if d.data == path_array[i]:
                continue

        return d

    def __delitem__(self, path):
        self[path].del_self()


if __name__ == "__main__":
    tree = DirectoryTree("/home/matej/workarea/matejc.myportal/src")

    a1 = tree.add("/home/matej/workarea/matejc.myportal/src")
    a2 = tree.add("/home/matej/workarea/matejc.myportal/src/matejc/myportal/profiles", True)
    a3 = tree.add("/home/matej/workarea/matejc.myportal/src/matejc/__init__.py")

    assert a2
    assert a3

    for n in tree:
        print n.get_path()
    print len(tree.root.children)

    assert "/home/matej/workarea/matejc.myportal/src/matejc/__init__.py" in tree
    assert "/home/matej/workarea/matejc.myportal/src/matejc/myportal/profiles/default/matejc.myportal.marker.txt" in tree

    g1 = tree["/home/matej/workarea/matejc.myportal/src/matejc/myportal/profiles/default/matejc.myportal.marker.txt"]
    print g1.get_path()

    assert tree["/home/matej/workarea/matejc.myportal/src/matejc/myportal/profiles/default/metadata.xml"]
    del tree["/home/matej/workarea/matejc.myportal/src/matejc/myportal/profiles/default/metadata.xml"]
    assert not tree["/home/matej/workarea/matejc.myportal/src/matejc/myportal/profiles/default/metadata.xml"]