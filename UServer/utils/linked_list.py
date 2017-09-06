class SinglyNode:
    def __init__(self, data):
        self.data = data
        self.next = None

    def set_next(self, node):
        if isinstance(node, SinglyNode):
            self.next = node
        else:
            raise TypeError('Expect an Node instance but %r got' % node)



class DoublyNode:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None


class SinglyLinkedList:
    def __init__(self, node):
        assert isinstance(node, SinglyNode)
        self.head = node
        self.head.next = None
        self.tail = self.head

    def add_node(self, node, position=-1):
        """
        :param node:
        :param position:-1: add node to tail T=O(1),
                         0: add node to head T=O(1),
                        >0: add node to specific position T=O(N)
                        <-1: add node to specific position T=O(2N)
        :return:
        """
        assert isinstance(position, int) and isinstance(node, SinglyNode)
        # if position == -1:
        #     self.tail.next = node
        #     self.tail = node
        if position == 0:
            node.next = self.head
            self.head = node
        elif position > 0:
            last_node = self.get_node(position-1)
            if last_node is None:
                raise IndexError('Index %d out of range' % position)
            node.next = last_node.next
            if node.next is None:
                self.tail = node
            last_node.next = node
        elif position < 0:
            last_node = self.get_node(position)
            if last_node is None:
                raise IndexError('Index %d out of range' % position)
            node.next = last_node.next
            if node.next is None:
                self.tail = node
            last_node.next = node

    def get_node(self, position):
        """
        :param position: if position >=0, T = O(N), elif position <0, T=O(2N)
        :return: Node
        """
        assert isinstance(position, int)
        if position == -1:
            return self.tail
        if position < -1:
            index = self.length() + position
        else:
            index = position
        if index >= 0:
            node = self.head
            while index:
                node = node.next
                index -= 1
                if node is None:
                    raise IndexError('Index %d out of range' % position)
            return node
        else:
            raise IndexError('Index %d out of range' % position)

    def length(self):
        """
        :return: int. T=O(N)
        """
        node = self.head
        count = 1
        while node.next is not None:
            count += 1
            node = node.next
        return count

    def to_list(self):
        ll = list()
        node = self.head
        while node:
            ll.append(node.data)
            node = node.next
        return ll

if __name__ == '__main__':
    ll = SinglyLinkedList(SinglyNode(0))
    ll.add_node(SinglyNode(1))
    ll.add_node(SinglyNode(2))
    ll.add_node(SinglyNode(3))
    ll.add_node(SinglyNode(4))
    print(ll.to_list())
    ll.add_node(SinglyNode(1.5), position=2)
    print(ll.to_list())
    # print(ll.tail.data)
    # print(ll.get_node(6).data)