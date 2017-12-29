import requests

requests.get('http://api.trustmile.com/consumer/v1/account/verifyEmail')




{
       Authorization = "Basic dHJ1c3RtaWxlOnd5aXNzOE9ybjY=";   
       "User-Agent" = "TrustMile-Consumer/1.0 (iPhone Simulator; iOS 8.4; Scale/2.00)";    
       "Content-Type" = "application/json";
}
TO URL => http://api.trustmile.com/consumer/v1/account/verifyEmail/testCodeSentToServer
HTTPMethod => GET

We got following response with status Code 400
{"message": 
    "The browser (or proxy) sent a request that this server could not understand."}

       2. While sending revivify request to server.
       Below are the request header sent
{
       Authorization = "Basic dHJ1c3RtaWxlOnd5aXNzOE9ybjY=";
          "Content-Type" = "application/json";    
           "User-Agent" = "TrustMile-Consumer/1.0 (iPhone Simulator; iOS 8.4; Scale/2.00)";    
           apiKey = c5c8b1de67be042849427bb1f562e687298bc73631829ce3a7b93984301a8972;
}
To URL => http://api.trustmile.com/consumer/v1/account/reverifyEmail
HTTPMethod => PUT
We got “Authentication failed"  “401”   in response

Please investigate and suggest us (edited)
