
import json
import PIL
from PIL import Image,ImageDraw
import socketserver





# this will show image in any image viewer

# Save the edited image


#img.save("car2.png")





class MyTCPHandler(socketserver.BaseRequestHandler):
    """
    The request handler class for our server.

    It is instantiated once per connection to the server, and must
    override the handle() method to implement communication to the
    client.
    """

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        #print("{} wrote:".format(self.client_address[0]))
        #print(self.data)
        to_str = self.data.decode()
        in_dict = json.loads(to_str)
        report =in_dict["NAME"] + ' Ocerdue: ' + str(in_dict["OVERDUE"]) + ' Day: ' + str(in_dict['CURRENT']) + ' Interval'+str(in_dict['PERIOD'])
        # creating image object which is of specific color
        img = PIL.Image.new(mode = "RGB", size = (600, 200),
                           color = (153, 153, 255))
        # Open an Image
        # Call draw Method to add 2D graphics in an image
        I1 = ImageDraw.Draw(img)
        # Add Text to an image
        I1.text((28, 36), report, fill=(255, 255, 0))
        # Display edited image
        img.show()
        img.save("T.png")

        
if __name__ == "__main__":
    HOST, PORT = "0.0.0.0", 31230
    # Create the server, binding to localhost on port 9999
    with socketserver.TCPServer((HOST, PORT), MyTCPHandler) as server:
        # Activate the server; this will keep running until you
        # interrupt the program with Ctrl-C
        server.serve_forever()
