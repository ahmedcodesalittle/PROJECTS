
import numpy as np
from tkinter import *
import os
from tkinter import filedialog
import cv2
import time
from matplotlib import pyplot as plt
from tkinter import messagebox


def endprogram():
	print ("\nProgram terminated!")
	sys.exit()




def testing():
    global testing_screen
    testing_screen = Toplevel(main_screen)
    testing_screen.title("Testing")
    # login_screen.geometry("400x300")
    testing_screen.geometry("600x450+650+150")
    testing_screen.minsize(120, 1)
    testing_screen.maxsize(1604, 881)
    testing_screen.resizable(1, 1)
    testing_screen.configure(bg='cyan')
    # login_screen.title("New Toplevel")

    Label(testing_screen, text='''Upload Image''', disabledforeground="#a3a3a3",
          foreground="#000000", width="300", height="2",bg='cyan', font=("Calibri", 16)).pack()
    Label(testing_screen, text="").pack()
    Label(testing_screen, text="").pack()
    Label(testing_screen, text="").pack()
    Button(testing_screen, text='''Upload Image''', font=(
        'Verdana', 15), height="2", width="30",bg='cyan', command=imgtest).pack()


global affect
def imgtest():


    import_file_path = filedialog.askopenfilename()

    image = cv2.imread(import_file_path)
    print(import_file_path)
    filename = 'Test.jpg'
    cv2.imwrite(filename, image)
    print("After saving image:")
    #result()

    #import_file_path = filedialog.askopenfilename()
    print(import_file_path)
    fnm = os.path.basename(import_file_path)
    print(os.path.basename(import_file_path))

   # file_sucess()

    print("\n*********************\nImage : " + fnm + "\n*********************")
    img = cv2.imread(import_file_path)
    if img is None:
        print('no data')

    img1 = cv2.imread(import_file_path)
    print(img.shape)
    img = cv2.resize(img, ((int)(img.shape[1] / 5), (int)(img.shape[0] / 5)))
    original = img.copy()
    neworiginal = img.copy()
    cv2.imshow('original', img1)
    gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)

    img1S = cv2.resize(img1, (960, 540))

    cv2.imshow('Original image', img1S)
    grayS = cv2.resize(gray, (960, 540))
    cv2.imshow('Gray image', grayS)

    dst = cv2.fastNlMeansDenoisingColored(img1, None, 10, 10, 7, 21)
    cv2.imshow("Noise Removal", dst)

    #import cv2
    import torch
    import numpy as np
    # Load the model
    model = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5/runs/train/exp6/weights/best.pt',
                           force_reload=True)
    #model.conf = 0.2
    # Set webcam input
    cam = cv2.VideoCapture(filename)
    dd1 = 0
    dd2 = 0
    dd3 = 0
    dd4 = 0
    while True:
        # Read frames
        ret, img = cam.read()
        dd2 += 1

        # Perform object detection
        results = model(img)
        # print(results)

        try:
            # Access the detection results
            class_names = ['lane', 'pedestrian', 'sign', 'trafficlight', 'vehicle']  # List of class names in the order corresponding to the model's output

            # Assuming results contains bounding box coordinates and class indices
            bounding_boxes = results.xyxy[0]  # Assuming the first image in results
            class_indices = bounding_boxes[:, -1].int().tolist()  # Extracting class indices
            # Mapping class indices to class names
            prediction_names = [class_names[idx] for idx in class_indices]
            # Printing prediction names
            print(prediction_names[0])

            if prediction_names[0] == "0":
                dd1 += 1
                import winsound
                filename1 = 'alert.wav'
                winsound.PlaySound(filename1, winsound.SND_FILENAME)
                cv2.imwrite("alert.jpg", img)
                sendmail()


        except:
            pass


        cv2.imshow("Output", np.squeeze(results.render()))

        # Press 'q' or 'Esc' to quit
        if (cv2.waitKey(1) & 0xFF == ord("q")) or (cv2.waitKey(1) == 27):
            break

    # Close the camera
    cam.release()
    cv2.destroyAllWindows()







def Camera():
    import_file_path = filedialog.askopenfilename()
    import cv2
    import torch
    import numpy as np
    # Load the model
    model = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5/runs/train/exp6/weights/best.pt',
                           force_reload=True)
    model.conf = 0.3
    # Set webcam input
    cam = cv2.VideoCapture(import_file_path)
    #cam = cv2.VideoCapture(0)
    dd1 = 0
    dd2 = 0
    dd3 = 0
    dd4 = 0
    while True:
        # Read frames
        ret, img = cam.read()
        dd2 += 1
        print(dd2)

        # Perform object detection

        # print(results)
        results = model(img)

        try:

            # Access the detection results
            class_names = ['lane', 'pedestrian', 'sign', 'trafficlight', 'vehicle']  # List of class names in the order corresponding to the model's output

            # Assuming results contains bounding box coordinates and class indices
            bounding_boxes = results.xyxy[0]  # Assuming the first image in results
            class_indices = bounding_boxes[:, -1].int().tolist()  # Extracting class indices
            # Mapping class indices to class names
            prediction_names = [class_names[idx] for idx in class_indices]
            # Printing prediction names
            print(prediction_names[0])

            if prediction_names[0] == "lane":
                dd2 = 0
            if prediction_names[0] =="":
                dd1 += 1





        except:
            pass

        if dd2 == 100:
            dd2 = 0

            import winsound
            filename = 'alert.wav'
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            #cv2.imwrite("alert.jpg", img)
            #sendmail()

        cv2.imshow("Output", np.squeeze(results.render()))

        # Press 'q' or 'Esc' to quit
        if (cv2.waitKey(1) & 0xFF == ord("q")) or (cv2.waitKey(1) == 27):
            break

    # Close the camera
    cam.release()
    cv2.destroyAllWindows()


def Camera1():
    #import_file_path = filedialog.askopenfilename()
    import cv2
    import torch
    import numpy as np
    # Load the model
    model = torch.hub.load('ultralytics/yolov5', 'custom', path='yolov5/runs/train/exp8/weights/best.pt',
                           force_reload=True)
    model.conf = 0.3
    # Set webcam input
    #cam = cv2.VideoCapture(import_file_path)
    cam = cv2.VideoCapture(0)
    dd1 = 0
    dd2 = 0
    dd3 = 0
    dd4 = 0
    while True:
        # Read frames
        ret, img = cam.read()
        #dd2 += 1
        print(dd2)

        # Perform object detection

        # print(results)
        results = model(img)

        try:

            # Access the detection results
            class_names = ['Pothole', 'SpeedBreaker']  # List of class names in the order corresponding to the model's output

            # Assuming results contains bounding box coordinates and class indices
            bounding_boxes = results.xyxy[0]  # Assuming the first image in results
            class_indices = bounding_boxes[:, -1].int().tolist()  # Extracting class indices
            # Mapping class indices to class names
            prediction_names = [class_names[idx] for idx in class_indices]
            # Printing prediction names
            print(prediction_names[0])

            if prediction_names[0] == "Pothole" or prediction_names[0] =="SpeedBreaker" :
                dd2 += 1






        except:
            pass

        if dd2 == 20:
            dd2 = 0

            import winsound
            filename = 'alert.wav'
            winsound.PlaySound(filename, winsound.SND_FILENAME)
            #cv2.imwrite("alert.jpg", img)
            #sendmail()

        cv2.imshow("Output", np.squeeze(results.render()))

        # Press 'q' or 'Esc' to quit
        if (cv2.waitKey(1) & 0xFF == ord("q")) or (cv2.waitKey(1) == 27):
            break

    # Close the camera
    cam.release()
    cv2.destroyAllWindows()


def sendmail():
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    fromaddr = "projectmailm@gmail.com"
    toaddr =  "sangeeth5535@gmail.com"

    # instance of MIMEMultipart
    msg = MIMEMultipart()

    # storing the senders email address
    msg['From'] = fromaddr

    # storing the receivers email address
    msg['To'] = toaddr

    # storing the subject
    msg['Subject'] = "Alert"

    # string to store the body of the mail
    body = "Ambulance  Detection"

    # attach the body with the msg instance
    msg.attach(MIMEText(body, 'plain'))

    # open the file to be sent
    filename = "alert.jpg"
    attachment = open("alert.jpg", "rb")

    # instance of MIMEBase and named as p
    p = MIMEBase('application', 'octet-stream')

    # To change the payload into encoded form
    p.set_payload((attachment).read())

    # encode into base64
    encoders.encode_base64(p)

    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)

    # attach the instance 'p' to instance 'msg'
    msg.attach(p)

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # Authentication
    s.login(fromaddr, "qmgn xecl bkqv musr")

    # Converts the Multipart msg into a string
    text = msg.as_string()

    # sending the mail
    s.sendmail(fromaddr, toaddr, text)

    # terminating the session
    s.quit()










def main_account_screen():
    global main_screen
    main_screen = Tk()
    width = 600
    height = 600
    screen_width = main_screen.winfo_screenwidth()
    screen_height = main_screen.winfo_screenheight()
    x = (screen_width / 2) - (width / 2)
    y = (screen_height / 2) - (height / 2)
    main_screen.geometry("%dx%d+%d+%d" % (width, height, x, y))
    main_screen.resizable(0, 0)
    # main_screen.geometry("300x250")
    main_screen.configure()
    main_screen.title(" Road Lane Detection ")

    Label(text="Road Lane Detection", width="300", height="5", font=("Calibri", 16)).pack()



    Label(text="").pack()
    Button(text="Lane & ObjectDetection", font=(
        'Verdana', 15), height="2", width="30", command=Camera).pack(side=TOP)
    Label(text="").pack()
    Button(text="SurfaceDetection", font=(
        'Verdana', 15), height="2", width="30", command=Camera1).pack(side=TOP)

    main_screen.mainloop()


main_account_screen()

