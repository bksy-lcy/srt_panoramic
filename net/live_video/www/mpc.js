//MultiMpcRule
var MultiMpcRule;

// Rule that selects the lowest possible bitrate
function MultiMpcRuleClass() {

   let factory = dashjs.FactoryMaker;
   let SwitchRequest = factory.getClassFactoryByName('SwitchRequest');
   let DashMetrics = factory.getSingletonFactoryByName('DashMetrics');
   let DashManifestModel = factory.getSingletonFactoryByName('DashManifestModel');
   let StreamController = factory.getSingletonFactoryByName('StreamController');
   let Debug = factory.getSingletonFactoryByName('Debug');

   let context = this.context;
   let instance,logger;

   let past_bandwidth = [],
       past_bandwidth_ests = [],
       past_error = [];

   let len_combos = [[],[],[],[]];
   let len_index = 1, last_buffer = 0;


   function setup() {
       logger = Debug(context).getInstance().getLogger(instance);
       combos = [[4,1], [2,2,1], [2,1,2], [2,1,1,1], [1,4], [1,2,2], [1,2,1,1], [1,1,2,1], [1,1,1,2], [1,1,1,1,1]];
       index = 1;
       let flag,now_tp;
       for (i=0;i<combos.length;i++){
           combo = combos[i];
           for (index=0;index<4;index++){
               flag=true;
               now_tp=index;
               for(j=0;j<combo.length;j++){
                   l=combo[j];
                   if(l==2 && now_tp%2==1){
                       flag=false;
                       break;
                   }
                   if(l==4 && now_tp>0){
                       flag=false;
                       break;
                   }
                   now_tp+=l;
                   now_tp%=4;
               }
               if(flag){
                   len_combos[index].push(combo);
               }
           }
       }
   }

   function getBestCombo(num_bitrate, future_length, future_bandwidth, curr_buffer, last_quality, rtt, _bitrateList){
       let sum,f_l,br_combos;
       let curr_rebuffer_time,curr_buffer_length,curr_quality,bitrate_sum,smoothness_diffs,tmp,chunk_size;
       let combo_reward,best_reward=-10000000,best_combo=[0,1];
       let bitrateList = [_bitrateList[0], _bitrateList[3], _bitrateList[6], _bitrateList[9], _bitrateList[12], _bitrateList[15]];
       for(ii=0;ii<len_combos[len_index].length;ii++){
           len_combo=len_combos[len_index][ii];
           sum = 0;
           f_l = 0;
           for(j=0;j<len_combo.length;j++){
               l=len_combo[j];
               sum += l;
               if(sum>future_length)
                   break;
               f_l++;
           }
           if(f_l==0)
               continue;
           br_combos = num_bitrate**f_l;
           for(br_combo=0;br_combo<br_combos;br_combo++){
               curr_rebuffer_time=0;
               curr_buffer_length=curr_buffer;
               curr_quality=last_quality;
               bitrate_sum=0;
               smoothness_diffs=0;
               tmp=br_combo;
               for(i=0;i<f_l;i++){
                   br = tmp%num_bitrate;
                   tmp=Math.floor(tmp/num_bitrate);
                   chunk_quality = bitrateList[br];
                   //估计chunk_size
                   chunk_size = bitrateList[br]*len_combo[i];
                   download_time = chunk_size/future_bandwidth+rtt;
                   if(curr_buffer_length<download_time){
                       curr_buffer_length = 0;
                       curr_rebuffer_time+=download_time-curr_buffer_length;
                   }else{
                       curr_buffer_length-=download_time;
                   }
                   curr_buffer_length+=len_combo[i];
                   bitrate_sum+=len_combo[i]*chunk_quality;
                   smoothness_diffs+=Math.abs(curr_quality-chunk_quality);
                   curr_quality=chunk_quality;
               }
               combo_reward = bitrate_sum/1000000 - 160.0*curr_rebuffer_time - 1.0*smoothness_diffs/1000000;
               if(combo_reward>best_reward){
                   best_reward=combo_reward;
                   best_combo=[br_combo%num_bitrate, len_combo[0]];
               }
           }
       }
       //best_combo[1]=1;
       len_index += best_combo[1];
       len_index %= 4;
       best_index = best_combo[0]*3+Math.floor(best_combo[1]/2);
       return best_index;
   }

   function getBytesLength(request) {
       return request.trace.reduce(function (a, b) {
           return a + b.b[0];
       }, 0);
   }
   function get_index(url) {
       let urls = url.split('/');
       urls = urls[urls.length-1].split('.')[0].split('chunk-stream')[1].split('-');
       let a=Number(urls[0]),b=Number(urls[1]);
       a %= 3;
       a++;
       if(a==3)
           a++;
       console.log(a,b,b*a);
       return b*a;
   }

   function get_current(url) {
       let urls = url.split('/');
       urls = urls[urls.length-1].split('.')[0].split('chunk-stream')[1].split('-')[0];
       return urls;
   }

   function getMaxIndex(rulesContext) {
       console.log("mympc");
       let mediaType = rulesContext.getMediaInfo().type;
       if(mediaType!="video"){
           return SwitchRequest(context).create();
       }
       let dashMetrics = DashMetrics(context).getInstance();
       let dashManifest = DashManifestModel(context).getInstance();
       let streamController = StreamController(context).getInstance();
       let abrController = rulesContext.getAbrController();
       let current = abrController.getQualityFor(mediaType, streamController.getActiveStreamInfo().id);
       let bitrateList = rulesContext.getMediaInfo().bitrateList.map(b => b.bandwidth);

       let requests = dashMetrics.getHttpRequests(mediaType),
           lastRequest = null,
           currentRequest = null,
           downloadTime,
           totalTime,
           rttTime,
           calculatedBandwidth,
           bufferLevel,
           past_len,
           err_len,
           harmonic_bandwidth,
           mx_err,
           future_bandwidth,

           i,
           q = SwitchRequest.NO_CHANGE,
           p = SwitchRequest.PRIORITY.DEFAULT,
           totalBytesLength = 0;

       bufferLevel = dashMetrics.getCurrentBufferLevel(mediaType);
       if (!requests) {
           return SwitchRequest(context).create();
       }
       i = requests.length - 1;
       while (i >= 0 && lastRequest === null) {
           currentRequest = requests[i];
           if (currentRequest._tfinish && currentRequest.trequest && currentRequest.tresponse && currentRequest.trace && currentRequest.trace.length > 0) {
               lastRequest = requests[i];
           }
           i--;
       }
       if (lastRequest === null) {
           return SwitchRequest(context).create();
       }
       if (lastRequest.type !== 'MediaSegment') {
           return SwitchRequest(context).create();
       }
       totalTime = (lastRequest._tfinish.getTime() - lastRequest.trequest.getTime()) / 1000.0;
       downloadTime = (lastRequest._tfinish.getTime() - lastRequest.tresponse.getTime()) / 1000.0;
       rttTime = (lastRequest.tresponse.getTime() - lastRequest.trequest.getTime()) / 1000.0;
       if (totalTime <= 0) {
           return SwitchRequest(context).create();
       }
       totalBytesLength = getBytesLength(lastRequest);
       totalBytesLength *= 8;
       calculatedBandwidth = true ? (totalBytesLength / totalTime) : (totalBytesLength / downloadTime);
       if (isNaN(calculatedBandwidth)) {
           return SwitchRequest(context).create();
       }
       past_bandwidth.push(calculatedBandwidth);
       curr_error = 0;
       if(past_bandwidth_ests.length>0){
           last_est = past_bandwidth_ests[past_bandwidth_ests.length-1];
           curr_error = Math.abs(calculatedBandwidth-last_est)/calculatedBandwidth;
       }
       past_error.push(curr_error);
       past_len = Math.min(5, past_bandwidth.length);
       err_len = Math.min(5, past_error.length);
       harmonic_bandwidth = 0
       for(i=1;i<=past_len;i++){
           harmonic_bandwidth+=1.0/past_bandwidth[past_bandwidth.length-i];
       }
       harmonic_bandwidth = past_len/harmonic_bandwidth;
       mx_err = past_error[past_error.length-1];
       for(i=2;i<=err_len;i++){
           mx_err=Math.max(mx_err, past_error[past_error.length-i]);
       }
       future_bandwidth = harmonic_bandwidth/1;
       past_bandwidth_ests.push(future_bandwidth);
       //len_index = get_index(lastRequest.url)%4;
       //current = get_current(lastRequest.url);
       let best_combo = getBestCombo(6, 5,future_bandwidth,bufferLevel,bitrateList[current],rttTime,bitrateList);
       q = best_combo;
       p = SwitchRequest.PRIORITY.STRONG;
       let cb=Math.floor(current/3),cl=current%3;
       cl++;
       if(cl==3)
           cl++;
       //console.log(rulesContext);
       //console.log(rulesContext.getMediaInfo());
       //console.log(rulesContext.getSwitchHistory().getSwitchRequests());
       //console.log(lastRequest.url);
       console.log(bitrateList[current]*cl/1000000, 160.0*(totalTime > last_buffer ? totalTime-last_buffer : 0), Math.abs(bitrateList[q]-bitrateList[current])/1000000, rttTime, calculatedBandwidth, bufferLevel, current, cl, cb);
       last_buffer = bufferLevel;
       return SwitchRequest(context).create(q, { name: MultiMpcRuleClass.__dashjs_factory_name }, p);
   }
   
   function reset(){
       len_index = 1;
       last_buffer = 0;
       past_bandwidth = [];
       past_bandwidth_ests = [];
       past_error = [];

   }

   instance = {
       getMaxIndex: getMaxIndex,
       reset: reset
   };

   setup();

   return instance;
}

MultiMpcRuleClass.__dashjs_factory_name = 'MultiMpcRule';
MultiMpcRule = dashjs.FactoryMaker.getClassFactory(MultiMpcRuleClass);

