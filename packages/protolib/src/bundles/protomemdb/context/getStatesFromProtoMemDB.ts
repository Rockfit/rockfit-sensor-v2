import { API, StateElement, StateGroup } from "protobase";
import { ProtoMemDB } from "protobase";

export const getStatesFromProtoMemDB = async (tag, useRemoteAPI?): Promise<StateGroup> => {
    let states
    if(useRemoteAPI) {
        states = (await API.get("/api/v1/protomemdb/" + tag)).data
    } else {
        states = await ProtoMemDB.getByTag(tag);
    }
    
    
    const stateGroup = new StateGroup(Object.entries(states).map(([key, value]) => {
        if(Array.isArray(value)) {
            return new StateGroup(value.map((state, i) => {
                return new StateElement(key+'_'+i, state)
            }), key)
        }
        return new StateElement(key, value);
    }), 'states');
    return stateGroup;
}