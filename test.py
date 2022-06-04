import sys
import os
from gitlab_module import *


def main(arguments):

    myProjectsFile=open("output.projects.json","w")
    myPipelinesFile=open("output.pipelines.json","w")
    myJobsFile=open("output.jobs.json","w")
    myProjectList=[4873]


    myGitlabName ="juniper-ssd-git"
    myGit=gitlab_api(myGitlabName)

    myversion, returncode = myGit.GET("version")
    #print(json.dumps(myversion,indent=22))


    for Item in myProjectList:

        myParsDict={"id": Item}
        print("--- GITLAB PROJECT ---") 
        myProject, returncode = myGit.GET("get_project_by_id",myParsDict)
        #print(json.dumps(myProject,indent=22))

        print("--- GITLAB PIPELINES ---") 
        myPipelines, returncode = myGit.GET("get_pipelines_by_projectid",myParsDict)
        #print(json.dumps(myPipelines,indent=22))  

        print("--- GITLAB JOBS FOR PIPELINE /1198919 ---") 
        myParsDict["pipeline_id"]=1198919
        myPipelineJobs, returncode = myGit.GET("get_jobs_by_pipelineid",myParsDict)
        print(json.dumps(myPipelineJobs,indent=22))  



if __name__ == '__main__':
    main(sys.argv)
