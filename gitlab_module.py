
import requests, json, jinja2,urllib3,logging
#from tinydb import TinyDB, Query
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

'''
#######Documentation:#########
"nims_gitlab_api" functionality to perform various API operation on the Gitlab. Which include following definition which can ve called over script

gitlab_api()
requires the following arrg/parameter to initialize the function definitions:
api_url: gitlab setup endpoint URL
api_token= API auth token


get_project_data()
The function definition can be used collecting information about the project(user token has access for)
sample: i/p merge_url: "/projects/"

get_merge_request_data()
The function definition can be used collecting the merge request status and info of a project 
sample i/p merge_url: "/projects/:id/merge_requests"

approve_merge_request()
The function definition can be used for approving a merge request
sample i/p merge_url: "/projects/:id/merge_requests/:merge_request_iid"

unapprove_merge_request()
The function definition can be used for unproved the previously approved merge request
sample i/p merge_url: "/projects/:id/merge_requests/:merge_request_iid"
'''

class gitlab_api():

    const_AppConfigFile="./configdata.json"

    def __init__(self,EndpointName,logger=None):
        self.log=logger or logging.getLogger(__name__)
        with open(self.const_AppConfigFile,"r") as configfile:
            self.configData = json.load(configfile)
        myDict=self.configData["GitLabEndpoint"]
        if EndpointName in myDict.keys():
            self.token=myDict[EndpointName]["AccessToken"]
            self.api_url=myDict[EndpointName]["GitLabURL"]
        else:
            print("ERROR : name of endpoint {:s} missing from configdata.json".format(EndpointName))
            exit(-1)
        if len(self.configData["GlobalSettings"]["OutputToFile"])>0:
            self.saveToFile=True
            self.myFiles={}
            for FileItem in self.configData["GlobalSettings"]["OutputToFile"]:
                myCategory=FileItem["category"]
                self.myFiles[myCategory]= open(FileItem["filename"],"w")



#---------------------------------------------------------------------------
    def GET(self,operationkey, variables={}):

        INITIALPAGEVALUE=1

        if operationkey not in self.configData["Operations"].keys():
            print("ERROR : requested operation key >{:s}< not in Operations dictionary".format(operationkey))
            print(self.configData["Operations"].keys())
            exit(-1)
        myOperation =self.configData["Operations"][operationkey]

        if "debug" in myOperation.keys():
            SetDebug=True
            print("SET DEBUG FOR ", operationkey)
        else:
            SetDebug=False
        HeaderDict={ 'Content-Type':'application/json','token': self.token,'Authorization':'Bearer '+self.token }

        apiurl=myOperation["apiurl"]
        myOpsCategory=myOperation["category"]
        
        apiurllist=list(filter(None,apiurl.split("/")))
        
        for key in variables.keys():
            try:
                value=variables[key]
                apiurllist[apiurllist.index(":"+ key)]=str(value)
            except:
                print ("Key-value variable {:}-{:} not found in apiurl {:} in json".format(key, value, apiurl))
                print(apiurllist)
                exit(-1)

        paramslist=[]
        #  GLOBAL PARAMETERS 
        for item in self.configData["Operations"]["globalparameters"]:
            for item2 in item.keys():
                    value= str(item[item2])
                    paramslist.append("?"+ item2+"="+value)  
        print(paramslist)

        #PER CATEGORY PARAMETERS
        for item in self.configData["Operations"]["percategoryparameters"]:

            if myOpsCategory in item.keys():
                    for item2 in item[myOpsCategory]:
                        for key in item2.keys():

                            value= str(item2[key])
                            paramslist.append("&"+ key+"="+value)   
        print(paramslist)


        #OPERATION SPECIFIC PARAMETERS
        if "parameters" in myOperation.keys():
            for item in myOperation["parameters"]:
                for item2 in item.keys():
                    value= str(item[item2])
                    paramslist.append("&"+ item2+"="+value)
        print(paramslist)
        
        ParamsString="/".join(apiurllist)+"".join(paramslist)
        ResultingURLString =self.api_url+ "/"+ ParamsString

       

     

        #print("RESULTINGURLSTRING=",ResultingURLString)
        GetMoreRecords=True
        PageCount=INITIALPAGEVALUE


        RequestObjectList=[]
        ResponseLink={
            "next":  {"url": ""}
                    }
        PageParameter="?page={:}".format(PageCount)
        ResponseLink["next"]["url"]=ResultingURLString+PageParameter
        while GetMoreRecords:

            if "next" in ResponseLink.keys():
                TotalURLString=ResponseLink["next"]["url"]
                SinglePageRequestObject = requests.get(url= TotalURLString , headers=HeaderDict)
                ResultType= type(SinglePageRequestObject.json())
                ResponseLink= SinglePageRequestObject.links

                if SetDebug:
                    print("------------------{:}----------{:}------------------".format(operationkey, PageCount))
                    if "next" in ResponseLink.keys():
                        print("Response links:",json.dumps(ResponseLink["next"],indent=22))
                    print("OPERATION : ", myOperation)
                #print("Pagecount:",PageCount)
                    print("Urlstring:",TotalURLString)
                    print("Status Code:",SinglePageRequestObject.status_code)
                    #print("JSON Single PageRequest response:",json.dumps(SinglePageRequestObject.json(),indent=22))
                #print("Len :", len(SinglePageRequestObject.json()))
                #print("Type of Singlepagerequest:", type(ResultType))


                if ResultType==list:
                    if PageCount==INITIALPAGEVALUE:
                        RequestObject=[]
                    RequestObject+=SinglePageRequestObject.json()
                else:
                    if PageCount==INITIALPAGEVALUE:
                        RequestObject={}
                    RequestObject.update(SinglePageRequestObject.json())
                PageCount+=1    
            else:
                GetMoreRecords=False
            

        if self.saveToFile:
            myOpsCategory=myOperation["category"]
            self.myFiles[myOpsCategory].write(json.dumps(RequestObject,indent=22))

        return RequestObject,SinglePageRequestObject.status_code


    def get_projects(self):
        projects=[]
        UrlString=self.api_url+"/projects"
        running_jobs = requests.get(url= UrlString , headers={ 'Content-Type':'application/json','token': self.token,'Authorization':'Bearer '+self.token ,'simple':'true'}, verify=False)
        if running_jobs.json() != []:
            for items in running_jobs.json():
                print(json.dumps(items, indent=22))
                projects.append(items)

        self.log.info('Project_ID_Response: %s',projects)
        return projects


    def get_project_data(self):
        project_data=[]
        pages="True"
        count=1
        while pages=="True":
            running_jobs = requests.get(url= self.api_url+"?page={}".format(count) , headers={ 'Content-Type':'application/json','token': self.token,'Authorization':'Bearer '+self.token }, verify=False)
            if running_jobs.json() != []:
                for items in running_jobs.json():
                    repo_data= {
                        "id":items['id'],
                        "name":items['name'],
                        "merge_re_url": items["_links"]["merge_requests"]
                    }
                    project_data.append(repo_data)
                count=count+1
            else:
                pages="False"
        self.log.info('Project_ID_Response: %s',project_data)
        return project_data

    def get_merge_request_data(self,merger_url):
        merge_request = requests.get(url= merger_url, headers={ 'Content-Type':'application/json','token': self.token,'Authorization':'Bearer '+self.token }, verify=False)
        self.log.info('Merge_request_Response: %s',merge_request)
        return merge_request.json()
    def get_merge_request_approval_status(self,merge_re_url,merge_id):
        merge_re_detailed_url= merge_re_url+"/"+str(merge_id)+"/approvals"
        #print(merge_re_detailed_url)
        merge_request_detailed = requests.get(url= merge_re_detailed_url, headers={ 'Content-Type':'application/json','token': self.token,'Authorization':'Bearer '+self.token }, verify=False)
        self.log.info('Merge_request_Response: %s',merge_request_detailed)
        approved_by="None"
        approvals=[]
        if merge_request_detailed.json()['approved_by']!=[]:
            for item in merge_request_detailed.json()['approved_by']:
                #print(item['user']['username'])
                approvals.append(item['user']['username'])
            approved_by=', '.join(approvals)
        return merge_request_detailed.json()['merge_status'],approved_by
    def approve_merge_request(self,merge_url):
        merge_request = requests.post(url= merge_url+"/approve", headers={ 'Content-Type':'application/json','token': self.token,'Authorization':'Bearer '+self.token }, verify=False)
        self.log.info('Merge_Apporve_Response: %s',merge_request)
        return merge_request
    def unapprove_merge_request(self,merge_url):
        merge_request = requests.post(url= merge_url+"/unapprove", headers={ 'Content-Type':'application/json','token': self.token,'Authorization':'Bearer '+self.token }, verify=False)
        self.log.info('Merge_Unapproved_Response: %s',merge_request)
        return merge_request
if __name__ == '__main__':
   gitlab_api()
