import rospy
from std_msgs.msg import String
import socket
import threading
import errno


# global variable
global mc_data
mc_data = ""


def get_mc_info(sock):
    # init random id
    id = 1
    single_json = []
    while True:

        try:
            # 1. get message and process
            raw_msg = sock.recv(MSG_SIZE)
            if raw_msg:

                # 2. split msg by newline
                messages = raw_msg.split("\n")
                for single_line in messages:
                    
                    # 3. keep storing to buffer
                    single_json.append(single_line)

                    # 4. if this is the end, of a single json
                    if single_line and single_line[-1] == "}":

                        # join as string
                        global mc_data
                        mc_data = "".join(single_json)
                        

                        # ready for next json
                        single_json = []

                        # print("MC_SUB=Received from MC={}, id={}".format(mc_data, id))
                        id+=1
            else:
                print("no response")
                break
        
        except socket.timeout as e:
            print("Timeout occurred while waiting for response: {}".format(e))
        
        except IOError as e:  
            if e.errno == errno.EPIPE:  
                print("broken pipe: {}".format(e))

def publish_mc_topic():
    
    # publish messages at 50 Hz
    rate = rospy.Rate(100)
    while not rospy.is_shutdown():
        msg = String()
        if mc_data:
            msg.data = mc_data
        else:
            msg.data = "no data yet"
        pub.publish(msg)
        rate.sleep()


if __name__ == "__main__":
    print("MC_SUB node is running...")

    # 1. init node
    rospy.init_node('mcsub_node')
    pub = rospy.Publisher('mc_topic',String, queue_size=10)

    # 2. init server socket to listen to client req
    HOST = socket.gethostname()
    MSG_SIZE = 1024
    MC_SUB_PORT = 9998

    MC_SUB_SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    MC_SUB_SERVER_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    MC_SUB_SERVER_SOCKET.bind((HOST, MC_SUB_PORT))
    MC_SUB_SERVER_SOCKET.listen(5)

    # 3. connect with new client (MC)
    client_socket, addr = MC_SUB_SERVER_SOCKET.accept()

    # start listening and logging in a separate thread
    listen_thread = threading.Thread(target=get_mc_info, args=(client_socket,))
    listen_thread.start()

    # start publishing messages in a separate thread
    publish_thread = threading.Thread(target=publish_mc_topic)
    publish_thread.start()

    # main loop
    while not rospy.is_shutdown():
        rospy.spin()
